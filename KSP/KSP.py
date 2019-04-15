from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import krpc
from enum import Enum

# Handles connection to kRPC
class KrpcClient(QThread):
    statusLabel_setText_trigger = pyqtSignal(['QString'])

    def __init__(self, statusLabel, parent=None):
        super().__init__(parent=parent)
        self.isConnected = False
        self.statusLabel_setText_trigger.connect(statusLabel.setText)
        self.statusLabel_setText_trigger.emit("Not Connected")

    def connect(self):
        try:
            self.conn = krpc.connect(name="KRPC Client")
            self.isConnected = True
            self.statusLabel_setText_trigger.emit("Connected")
        except:
            self.isConnected = False
            self.statusLabel_setText_trigger.emit("Not Connected")

    def run(self):
        self.exitThread = False
        while not self.exitThread:
            if not self.isConnected:
                self.connect()
            else:
                try:
                    vessel = self.conn.space_center.active_vessel
                    self.statusLabel_setText_trigger.emit("On Launchpad")
                except:
                    self.statusLabel_setText_trigger.emit("In VAB")


    def __del__(self):
        self.exit()

# Qt callbacks
def on_exitPushbutton_clicked():
    app.closeAllWindows()
    exit()

def on_connectPushbutton_clicked():
    krpcClient.connect()

# Main
if __name__ == "__main__":
    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout()

    statusLabel = QLabel()
    layout.addWidget(statusLabel)

    connectPushbutton = QPushButton("Connect")
    connectPushbutton.clicked.connect(on_connectPushbutton_clicked)
    layout.addWidget(connectPushbutton)

    exitPushbutton = QPushButton("Exit")
    exitPushbutton.clicked.connect(on_exitPushbutton_clicked)
    layout.addWidget(exitPushbutton)

    krpcClient = KrpcClient(statusLabel)
    krpcClient.start()

    window.setLayout(layout)
    window.show()

    app.exec_()
