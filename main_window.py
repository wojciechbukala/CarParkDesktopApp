import cv2
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
from main_window_ui import Ui_MainWindow
from receive import Receive

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.home_button.clicked.connect(self.display_home_page)
        self.current_state_button.clicked.connect(self.display_current_state_page)
        self.streaming_active = False

        self.display_home_page()

    def InitReceivingThread(self):
        self.receive_thread = Receive()
        self.receive_thread.update_frame.connect(self.update_image)
        self.receive_thread.start()
    
    def stop_streaming(self):
        if self.streaming_active == True:
            self.receive_thread.stop()

    def update_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame.data, 640, 480, QImage.Format_RGB888)
        img_scaled = img.scaled(480, 360, QtCore.Qt.KeepAspectRatio)
        self.video.setPixmap(QPixmap.fromImage(img_scaled))
        
    def display_home_page(self):
        self.stop_streaming()
        self.content.setCurrentWidget(self.home_page)
        self.streaming_active = True
        self.InitReceivingThread()

    def display_current_state_page(self):
        self.stop_streaming()
        self.content.setCurrentWidget(self.current_state_page)

    def closeEvent(self, event):
        self.receive_thread.stop()
        event.accept()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())