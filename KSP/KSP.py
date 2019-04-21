from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtChart import *
import krpc
import time

# Handles connection to kRPC
class KrpcClient(QThread):
    statusLabel_setText_trigger = pyqtSignal(['QString'])
    launchPushButton_setEnabled_trigger = pyqtSignal(bool)

    def __init__(self, statusLabel, launchPushbutton, parent=None):
        super().__init__(parent=parent)
        self.isConnected = False
        self.isFlying = False
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
        self.isFlying = True
        altitudeChart.start()

    # Thread loop
    def run(self):
        self.exitThread = False
        while not self.exitThread:
            if not self.isConnected:
                self.connect()
            else:
                # Server Connection Successful
                try:
                    self.vessel = self.conn.space_center.active_vessel
                except:
                    self.statusLabel_setText_trigger.emit("In VAB")
                    self.launchPushButton_setEnabled_trigger.emit(False)
                    self.isFlying = False;
                    continue
                # Vessel exists
                if not self.isFlying:
                    self.statusLabel_setText_trigger.emit("On Launchpad")
                    self.launchPushButton_setEnabled_trigger.emit(True)
                    stage = 0
                else:
                    self.statusLabel_setText_trigger.emit("Flying")
                    self.launchPushButton_setEnabled_trigger.emit(False)
                    # Check next stage
                    while stage is 0:
                        fuel_amount = self.conn.get_call(self.vessel.resources.amount, "Solid Fuel")
                        expr = self.conn.krpc.Expression.less_than(self.conn.krpc.Expression.call(fuel_amount), self.conn.krpc.Expression.constant_float(0.1))
                        event = self.conn.krpc.add_event(expr)
                        with event.condition:
                            event.wait()
                        self.vessel.control.activate_next_stage()
                        self.statusLabel_setText_trigger.emit("Staged")
                        stage += 1
                    while stage is 1:
                        time.sleep(1)
                        tick = 0
                        #altitudeData.append(tick, 3)
                        #altitudeChart.addSeries(altitudeData)
                        #altitudeChart.createDefaultAxes()


    def __del__(self):
        self.exit()

class Chart(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.chart = QChart()
        self.chartView = QChartView(self.chart)
        self.chart.legend().hide()
        self.chartView.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(self.chartView)

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
    layout = QVBoxLayout()

    statusLabel = QLabel()
    layout.addWidget(statusLabel)

    launchPushbutton = QPushButton("Launch")
    launchPushbutton.setEnabled(False)
    launchPushbutton.clicked.connect(on_launchPushbutton_clicked)
    layout.addWidget(launchPushbutton)

    krpcClient = KrpcClient(statusLabel, launchPushbutton)
    krpcClient.start()

    altitudeChart = AltitudeChart()

    window.setLayout(layout)
    window.show()

    app.exec_()
