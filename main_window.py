import cv2
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
from main_window_ui import Ui_MainWindow
from receive import Receive
from app_settings import settings
from db_selects import Selects

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

    def clear_table(self):
        self.CarsTable.setRowCount(0)

    def on_switch(self):
        self.stop_streaming()
        self.clear_table()

    def update_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame.data, 640, 480, QImage.Format_RGB888)
        img_scaled = img.scaled(480, 360, QtCore.Qt.KeepAspectRatio)
        self.video.setPixmap(QPixmap.fromImage(img_scaled))

    def update_table(self):
        selects = Selects()
        cars_table =  selects.get_current_cars()
        cars_table_len = len(cars_table)

        self.CarsTable.setRowCount(cars_table_lens)

        for i in range(0, cars_table_len):
            self.CarsTable.insertRow(i)
            for j in range(0, 4):
                self.CarsTable.setItem(i, j, QtWidgets.QTableWidgetItem(str(cars_table[i][j])))
    
    def display_home_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.home_page)
        self.streaming_active = True
        self.InitReceivingThread()

    def display_current_state_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.current_state_page)
        self.update_table()

    
    def closeEvent(self, event):
        self.receive_thread.stop()
        event.accept()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())