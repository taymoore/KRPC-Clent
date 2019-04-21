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

    #chart = QChart()
    #chart.legend().hide()
    #chartView = QChartView(chart)

    #chartView.setRenderHint(QPainter.Antialiasing)
    #layout.addWidget(chartView)

    #altitudeData = QLineSeries()
    #pen = altitudeData.pen()
    #pen.setWidthF(1)
    #altitudeData.setPen(pen)
    #altitudeData.setUseOpenGL(True)
    #altitudeData.append(1,1)
    #altitudeData.append(2,3)
    #chart.addSeries(altitudeData)
    #altitudeData.append(4,0)
    #axisX = QValueAxis()
    #axisX.setRange(0,5)
    #axisX.setTickCount(5)
    #chart.setAxisX(axisX)
    #altitudeData.attachAxis(axisX)
    #axisY = QValueAxis()
    #axisY.setRange(0,5)
    #axisY.setTickCount(5)
    #chart.setAxisY(axisY)
    #altitudeData.attachAxis(axisY)
    ##altitudeChart.createDefaultAxes()
    ##altitudeChartView.repaint()
    ##altitudeChart.update()


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
        self.axisX.setRange(0,5)
        self.axisX.setTickCount(5)
        self.chart.setAxisX(self.axisX)
        self.dataSeries.attachAxis(self.axisX)
        self.axisY = QValueAxis()
        self.axisY.setRange(0,5)
        self.axisY.setTickCount(5)
        self.chart.setAxisY(self.axisY)
        self.dataSeries.attachAxis(self.axisY)

    def addData(self, x, y):
        self.dataSeries.append(x,y)


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

    #krpcClient = KrpcClient(statusLabel, launchPushbutton)
    #krpcClient.start()

    altitudeChart = Chart()
    altitudeChart.addData(0,1)
    altitudeChart.addData(1,2)
    altitudeChart.addData(2,0)

    window.setLayout(layout)
    window.show()

    app.exec_()
