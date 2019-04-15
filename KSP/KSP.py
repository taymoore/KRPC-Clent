from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
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
                    #fuel_amount = self.conn.get_call(self.vessel.resources.amount, 'SolidFuel')
                    #expr = self.conn.krpc.Expression.less_than(
                    #    self.conn.krpc.Expression.call(fuel_amount),
                    #    self.conn.krpc.Expression.constant_float(0.5))
                    #event = self.conn.krpc.add_event(expr)
                    #with event.condition:
                    #    event.wait()
                    #print('Booster separation')
                    #self.vessel.control.activate_next_stage()
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


    def __del__(self):
        self.exit()

# Qt callbacks
def on_launchPushbutton_clicked():
    krpcClient.launch()

# Main
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout()

    statusLabel = QLabel()
    layout.addWidget(statusLabel)

    launchPushbutton = QPushButton("Launch")
    launchPushbutton.setEnabled(False)
    launchPushbutton.clicked.connect(on_launchPushbutton_clicked)
    layout.addWidget(launchPushbutton)

    krpcClient = KrpcClient(statusLabel, launchPushbutton)
    krpcClient.start()

    window.setLayout(layout)
    window.show()

    app.exec_()
