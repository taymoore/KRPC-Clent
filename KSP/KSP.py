from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import krpc
from enum import Enum
from multiprocessing import Process

# Handles connection to kRPC
class KrpcClient(QObject):
    statusLabel_setText_trigger = pyqtSignal(['QString'])

    def __init__(self, statusLabel, parent=None):
        super().__init__(parent=parent)
        self.isConnected = False
        self.statusLabel_setText_trigger.connect(statusLabel.setText)
        #self.connectThread = self.ConnectThread()
        #self.connect(self.connectThread, QtCore.SIGNAL("statusLabel_setText(QString)"), statusLabel.setText)

    def connect(self):
        try:
            self.conn = krpc.connect(name="Hello World")
            vessel = self.conn.space_center.active_vessel
            #print("connected to " + vessel.name)
            #statusLabel.setText("Connected")
            #self.emit(QtCore.SIGNAL("statusLabel_setText(QString)"), "Connected")
            self.isConnected = True
            self.statusLabel_setText_trigger.emit("Connected")
        except:
            #print("Failed to connect to KRPC server")
            #statusLabel.setText("Not Connected!")
            #self.emit(QtCore.SIGNAL("statusLabel_setText(QString)"), "Not Connected")
            self.isConnected = False
            self.statusLabel_setText_trigger.emit("Not Connected")

    #class ConnectThread(QThread):
    #    def __del__(self):
    #        self.exit()

    #    def run(self):
    #        while not self.isConnected and not self.exiting:
    #            self.connect()

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

    window.setLayout(layout)
    window.show()

    app.exec_()
