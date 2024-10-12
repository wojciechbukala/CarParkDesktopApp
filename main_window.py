import cv2
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
from main_window_ui import Ui_MainWindow
from receive import Receive
from app_settings import settings
from db_selects import Selects
from db_inserts import Inserts
from datetime import datetime
import json

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.home_button.clicked.connect(self.display_home_page)
        self.current_state_button.clicked.connect(self.display_current_state_page)
        self.auth_list_button.clicked.connect(self.display_auth_list_page)
        self.settings_button.clicked.connect(self.display_settings_page)
        self.streaming_active = False

        self.settings = self.read_settings()

        self.display_home_page()

    def read_settings(self):
        with open('settings/settings.json', 'r') as f:
            settings = json.load(f)
        return settings

    # reciving video stream
    def InitReceivingThread(self):
        self.receive_thread = Receive()
        self.receive_thread.update_frame.connect(self.update_image)
        self.receive_thread.start()
    
    #on switch page methods
    def stop_streaming(self):
        if self.streaming_active == True:
            self.receive_thread.stop()

    def clear_table(self):
        self.CarsTable.setRowCount(0)

    def on_switch(self):
        self.stop_streaming()
        self.clear_table()

    # video frames
    def update_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame.data, 640, 480, QImage.Format_RGB888)
        img_scaled = img.scaled(480, 360, QtCore.Qt.KeepAspectRatio)
        self.video.setPixmap(QPixmap.fromImage(img_scaled))

    # current state table
    def update_table(self):
        selects = Selects()
        cars_table =  selects.get_current_cars()
        cars_table_len = len(cars_table)

        self.CarsTable.setRowCount(cars_table_len)

        for i in range(0, cars_table_len):
            self.CarsTable.insertRow(i)
            for j in range(0, 4):
                self.CarsTable.setItem(i, j, QtWidgets.QTableWidgetItem(str(cars_table[i][j])))
    
    # add new auth car
    def on_auth_submit(self):
        self.update_auth_table()
        insert = Inserts()
        license_plate = self.lineEdit.text()
        start_qdate = self.dateEdit.date()
        end_qdate = self.dateEdit_2.date()

        start_date = datetime.combine(start_qdate.toPyDate(),  datetime.min.time())
        end_date = datetime.combine(end_qdate.toPyDate(),  datetime.min.time())

        now = datetime.now()

        if start_date >= now and end_date >= now:
            insert.insert_auth_car(license_plate, start_date, end_date)

            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Data Submitted")
            msg_box.setText("Data written")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Error")
            msg_box.setText("Check dates and try again!")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    # auth car table
    def update_auth_table(self):
        selects = Selects()
        cars_table =  selects.get_auth_cars()
        cars_table_len = len(cars_table)

        self.auth_table.setRowCount(cars_table_len)

        for i in range(0, cars_table_len):
            self.auth_table.insertRow(i)
            for j in range(0, 3):
                self.auth_table.setItem(i, j, QtWidgets.QTableWidgetItem(str(cars_table[i][j])))

    def display_home_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.home_page)
        self.streaming_active = True
        self.InitReceivingThread()

    def display_current_state_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.current_state_page)
        self.update_table()

    def display_auth_list_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.auth_list_page)
        self.update_auth_table()
        self.authSubmit.clicked.connect(self.on_auth_submit)

    def update_settings(self):
        management_settings = self.settings.get("management_settings", {})

        entrance_mode = management_settings.get("entrance_mode", "anyone")
        if entrance_mode == "anyone":
            self.anyone.setChecked(True)
        elif entrance_mode == "authorized":
            self.authorized.setChecked(True)

        payment_mode = management_settings.get("payment_mode", "free")
        if payment_mode == "free":
            self.free.setChecked(True)
        elif payment_mode == "entrance_fee":
            self.entrance_fee.setChecked(True)
        elif payment_mode == "fee_per_hour":
            self.per_hour.setChecked(True)

        fee_per_hour_val = management_settings.get("fee_per_hour", 0.0)
        self.fee_per_hour_input.setValue(fee_per_hour_val)

        connection_settings = self.settings.get("connection_settings", {})
        
        video_ip = connection_settings.get("video", {}).get("ip", "0.0.0.0")
        video_port = connection_settings.get("video", {}).get("port", 0)
        self.video_ip.setText(video_ip)
        self.video_port.setText(str(video_port))

        data1_ip = connection_settings.get("data1", {}).get("ip", "0.0.0.0")
        data1_port = connection_settings.get("data1", {}).get("port", 0)
        self.data1_ip.setText(data1_ip)
        self.data1_port.setText(str(data1_port))

        data2_ip = connection_settings.get("data2", {}).get("ip", "0.0.0.0")
        data2_port = connection_settings.get("data2", {}).get("port", 0)
        self.data2_ip.setText(data2_ip)
        self.data2_port.setText(str(data2_port))

        recognition_settings = self.settings.get("recognition_settings", {})
        recognition_confidence = recognition_settings.get("recognition_confidence", 50)
        self.conf_box.setValue(recognition_confidence)

    def on_submit_button(self):
        management_settings = {}

        if self.anyone.isChecked():
            management_settings["entrance_mode"] = "anyone"
        elif self.authorized.isChecked():
            management_settings["entrance_mode"] = "authorized"

        if self.free.isChecked():
            management_settings["payment_mode"] = "free"
        elif self.entrance_fee.isChecked():
            management_settings["payment_mode"] = "entrance_fee"
        elif self.per_hour.isChecked():
            management_settings["payment_mode"] = "fee_per_hour"

        management_settings["fee_per_hour"] = self.fee_per_hour_input.value()

        connection_settings = {}
        
        connection_settings.setdefault("video", {})
        connection_settings["video"]["ip"] = self.video_ip.text()
        connection_settings["video"]["port"] = self.video_port.text()

        connection_settings.setdefault("data1", {})
        connection_settings["data1"]["ip"] = self.data1_ip.text()
        connection_settings["data1"]["port"] = self.data1_port.text()

        connection_settings.setdefault("data2", {})
        connection_settings["data2"]["ip"] = self.data2_ip.text()
        connection_settings["data2"]["port"] = self.data2_port.text()

        self.settings["management_settings"] = management_settings
        self.settings["connection_settings"] = connection_settings

        with open("settings/settings.json", 'w') as f:
            json.dump(self.settings, f, indent=4)
        
    def on_reset_button(self):
    def display_settings_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.settings_page)
        self.update_settings()
        #self.reset_button.clicked.connect(self.on_reset_settings)
        self.submit_button.clicked.connect(self.on_submit_button)

    
    def closeEvent(self, event):
        self.receive_thread.stop()
        event.accept()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())