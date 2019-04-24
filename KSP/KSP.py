from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *
import krpc
import time

# Handles connection to kRPC
class KrpcClient(QThread):
    statusLabel_setText_trigger = pyqtSignal(['QString']) # For some reason, pyqtSignal can't be in constructor
    launchPushButton_setEnabled_trigger = pyqtSignal(bool)

    def __init__(self, statusLabel, launchPushbutton, parent=None):
        super().__init__(parent=parent)
        self.isConnected = False
        #self.isFlying = False
        self.statusLabel_setText_trigger.connect(statusLabel.setText)
        self.statusLabel_setText_trigger.emit("Not Connected")
        self.launchPushButton_setEnabled_trigger.connect(launchPushbutton.setEnabled)

    def connect(self):
        try:
            self.conn = krpc.connect(name="KRPC Client")
            self.isConnected = True
            self.statusLabel_setText_trigger.emit("Connected")
        except:
            self.isConnected = False
            self.statusLabel_setText_trigger.emit("Not Connected")

    def launch(self):
        self.vessel.control.throttle = 1
        self.vessel.control.activate_next_stage()
        #self.isFlying = True
        #stageComputer.start()
        altitudeChart.start()

    # Thread loop
    def run(self):
        self.exitThread = False
        while not self.exitThread:
            if not self.isConnected:
                self.connect()
            else:
                try:
                    gameScene = self.conn.krpc.current_game_scene
                    if gameScene.name == 'flight':
                        self.vessel = self.conn.space_center.active_vessel
                        self.launchPushButton_setEnabled_trigger.emit(True)
                        self.statusLabel_setText_trigger.emit("In Flight")
                        stageComputer.start()
                    elif gameScene.name == 'editor_vab':
                        self.launchPushButton_setEnabled_trigger.emit(False)
                        self.statusLabel_setText_trigger.emit("In VAB")
                        stageComputer.stop()
                    elif gameScene.name == 'space_center':
                        self.launchPushButton_setEnabled_trigger.emit(False)
                        self.statusLabel_setText_trigger.emit("Looking at Space Centre")
                        stageComputer.stop()
                    elif gameScene.name == 'tracking_station':
                        self.launchPushButton_setEnabled_trigger.emit(False)
                        self.statusLabel_setText_trigger.emit("In Tracking Station")
                        stageComputer.stop()
                    elif gameScene.name == 'editor_sph':
                        self.launchPushButton_setEnabled_trigger.emit(False)
                        self.statusLabel_setText_trigger.emit("In Space Plane Hangar")
                        stageComputer.stop()
                    else:
                        self.statusLabel_setText_trigger.emit("I have no clue where I am..")
                except:
                    self.isFlying = False
                time.sleep(1)
                ## Server Connection Successful
                #try:
                #    self.vessel = self.conn.space_center.active_vessel
                #except:
                #    self.statusLabel_setText_trigger.emit("In VAB")
                #    self.launchPushButton_setEnabled_trigger.emit(False)
                #    self.isFlying = False;
                #    continue
                ## Vessel exists
                #if not self.isFlying:
                #    self.statusLabel_setText_trigger.emit("On Launchpad")
                #    self.launchPushButton_setEnabled_trigger.emit(True)
                #    stage = 0
                #else:
                #    self.statusLabel_setText_trigger.emit("Flying")
                #    self.launchPushButton_setEnabled_trigger.emit(False)
                #    # Check next stage
                #    while stage is 0:
                #        fuel_amount = self.conn.get_call(self.vessel.resources.amount, "Solid Fuel")
                #        expr = self.conn.krpc.Expression.less_than(self.conn.krpc.Expression.call(fuel_amount), self.conn.krpc.Expression.constant_float(0.1))
                #        event = self.conn.krpc.add_event(expr)
                #        with event.condition:
                #            event.wait()
                #        self.vessel.control.activate_next_stage()
                #        self.statusLabel_setText_trigger.emit("Staged")
                #        stage += 1
                #    while stage is 1:
                #        time.sleep(1)
                #        tick = 0


    def __del__(self):
        self.exit()

class StageComputer(QThread):
    fuelProgressbar_setValue_trigger = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.isActive = False
        self.fuelProgressbar_setValue_trigger.connect(fuelProgressbar.setValue)

    def run(self):
        conn = krpc.connect(name="Staging Computer")
        vessel = conn.space_center.active_vessel
        self.isActive = True
        #Determine resources in each stage
        stageResources = []
        # For each stage
        for x in range(0, 10):
            # Get parts in stage
            if x == 0:
                stageGroup = vessel.parts.in_decouple_stage(-1)
            else:
                stageGroup = vessel.parts.in_decouple_stage(x)
            # If we have parts in this stage
            if(len(stageGroup) > 0):
                stageResources.append(dict())
                # For each part
                for part in stageGroup:
                    # Get resources in part
                    resources = part.resources
                    # For resources we care about
                    resourceNames = {"SolidFuel", "Aniline", "Furfuryl", "IRFNA-III"}
                    for resourceName in resourceNames:
                        # If the part has that resource
                        if resources.has_resource(resourceName):
                            # Record resource
                            stageResources[x][resourceName] = resources.amount(resourceName)
                            print("Stage " + str(x) + ": added " + resourceName + ": " + str(resources.amount(resourceName)))
            # Else we don't have parts in this stage
            else:
                break
        print("We have " + str(len(stageResources)) + " stages")
        while self.isActive:
            stageNum = len(stageResources)
            #Find largest fuel value
            fuelName = str()
            fuelValMax = 0
            for resourceName, resourceValMax in stageResources[stageNum-1].items():
                if resourceValMax > fuelValMax:
                    fuelName = resourceName
                    fuelValMax = resourceValMax
            fuelProgressbar.setMaximum(fuelValMax)
            with conn.stream(vessel.resources.amount, fuelName) as fuelVal:
                while self.isActive:
                    #fuelProgressbar.setValue(fuelVal())
                    self.fuelProgressbar_setValue_trigger.emit(fuelVal())
                    #print("Has " + str(fuelVal()))
        conn.close()

    def stop(self):
        self.isActive = False

# Charting
class Chart(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.chart = QChart()
        self.chartView = QChartView(self.chart)
        self.chart.legend().hide()
        self.chartView.setRenderHint(QPainter.Antialiasing)

        self.dataSeries = QLineSeries()
        pen = self.dataSeries.pen()
        pen.setWidth(1)
        self.dataSeries.setPen(pen)
        self.dataSeries.setUseOpenGL(True)
        self.chart.addSeries(self.dataSeries)
        self.axisX = QValueAxis()
        self.axisXMin = 0
        self.axisXMax = 1
        self.axisX.setRange(self.axisXMin,self.axisXMax)
        self.axisX.setTickCount(5)
        self.chart.setAxisX(self.axisX)
        self.dataSeries.attachAxis(self.axisX)
        self.axisY = QValueAxis()
        self.axisYMin = 0
        self.axisYMax = 1
        self.axisY.setRange(self.axisYMin,self.axisYMax)
        self.axisY.setTickCount(5)
        self.chart.setAxisY(self.axisY)
        self.dataSeries.attachAxis(self.axisY)

    def addData(self, x, y):
        self.dataSeries.append(x,y)
        if(self.axisXMax < x):
            self.axisXMax = x
            self.axisX.setRange(self.axisXMin,self.axisXMax)
        if(self.axisYMax < y):
            self.axisYMax = y
            self.axisY.setRange(self.axisYMin,self.axisYMax)

class AltitudeChart(Chart):
    @pyqtSlot()
    def timeoutCallback(self):
        self.addData((QDateTime.currentMSecsSinceEpoch() - self.launchTime)/1000, krpcClient.vessel.flight(krpcClient.vessel.orbit.body.reference_frame).mean_altitude)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.timeoutCallback)
        self.timer.setInterval(100)

    def start(self):
        self.timer.start()
        self.launchTime = QDateTime.currentMSecsSinceEpoch()

    def stop(self):
        self.timer.stop()

# Qt callbacks
def on_launchPushbutton_clicked():
    krpcClient.launch()

# Main
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    window.setMinimumSize(800, 500)
    vLayout = QVBoxLayout()

    statusLabel = QLabel()
    vLayout.addWidget(statusLabel)

    launchPushbutton = QPushButton("Launch")
    launchPushbutton.setEnabled(False)
    launchPushbutton.clicked.connect(on_launchPushbutton_clicked)
    vLayout.addWidget(launchPushbutton)

    hLayout = QHBoxLayout()
    vLayout.addLayout(hLayout)

    fuelProgressbar = QProgressBar()
    fuelProgressbar.setOrientation(Qt.Vertical)
    #fuelProgressbar.setFormat()
    hLayout.addWidget(fuelProgressbar)

    altitudeChart = AltitudeChart()
    hLayout.addWidget(altitudeChart.chartView)

    krpcClient = KrpcClient(statusLabel, launchPushbutton)
    krpcClient.start()

    stageComputer = StageComputer()


    window.setLayout(vLayout)
    window.show()

    app.exec_()
