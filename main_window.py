import cv2
import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTime, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from main_window_ui import Ui_MainWindow
from database.receive_video import ReceiveVideo
import database.read_database as rd
import database.write_to_database as wtd
from datetime import datetime
import json
import threading
import requests
from functools import partial
import settings.handle_settings as st
import time

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.home_button.clicked.connect(self.display_home_page)
        self.current_state_button.clicked.connect(self.display_current_state_page)
        self.auth_list_button.clicked.connect(self.display_auth_list_page)
        self.analitics_button.clicked.connect(self.display_analitics_page)
        self.database_button.clicked.connect(self.display_settings_page)
        self.settings_button.clicked.connect(self.display_settings_page)
        self.gpio_button.clicked.connect(self.display_gpio_page)
        self.refresh_button.clicked.connect(self.handle_refresh)
        self.streaming_active = False
        self.receiving_license_plate_active = False
        self.receiving_lp_data_active = False
        
        self.auth_submit_connected = False

        st.read_settings()
        self.database_address = f'{st.settings["connection_settings"]["database"]["ip"]}:{st.settings["connection_settings"]["database"]["port"]}'

        self.database_button.setText(self.database_address)
        self.database_connected = False

        self.database_check_timer = QTimer()
        self.database_check_timer.timeout.connect(self.check_server)
        self.database_check_timer.start(3000)

        self.display_home_page()

        self.UI_improvements()

    def UI_improvements(self):
        self.recognition_model.addItem("best.pt")
        self.recognition_model.addItem("other.pt")

        self.input1_type.addItem(" - ")
        self.input1_type.addItem("switch-on")
        self.input1_type.addItem("switch-off")
        self.input1_type.addItem("binary gate state")

        self.input2_type.addItem(" - ")
        self.input2_type.addItem("switch-on")
        self.input2_type.addItem("switch-off")
        self.input2_type.addItem("binary gate state")

        self.input3_type.addItem(" - ")
        self.input3_type.addItem("switch-on")
        self.input3_type.addItem("switch-off")
        self.input3_type.addItem("binary gate state")

        self.input4_type.addItem(" - ")
        self.input4_type.addItem("switch-on")
        self.input4_type.addItem("switch-off")
        self.input4_type.addItem("binary gate state")

        self.input5_type.addItem(" - ")
        self.input5_type.addItem("switch-on")
        self.input5_type.addItem("switch-off")
        self.input5_type.addItem("binary gate state")

        self.input6_type.addItem(" - ")
        self.input6_type.addItem("switch-on")
        self.input6_type.addItem("switch-off")
        self.input6_type.addItem("binary gate state")

        self.output1_type.addItem(" - ")
        self.output1_type.addItem("gate open")
        self.output1_type.addItem("gate close")
        self.output1_type.addItem("gate switch state")

        self.output2_type.addItem(" - ")
        self.output2_type.addItem("gate open")
        self.output2_type.addItem("gate close")
        self.output2_type.addItem("gate switch state")
                
        self.output3_type.addItem(" - ")
        self.output3_type.addItem("gate open")
        self.output3_type.addItem("gate close")
        self.output3_type.addItem("gate switch state")
                
        self.output4_type.addItem(" - ")
        self.output4_type.addItem("gate open")
        self.output4_type.addItem("gate close")
        self.output4_type.addItem("gate switch state")
                
        self.output5_type.addItem(" - ")
        self.output5_type.addItem("gate open")
        self.output5_type.addItem("gate close")
        self.output5_type.addItem("gate switch state")

        self.output6_type.addItem(" - ")
        self.output6_type.addItem("gate open")
        self.output6_type.addItem("gate close")
        self.output6_type.addItem("gate switch state")

        self.synchronization_warning.hide()

    def check_server(self):
        def check():
            try:
                response = requests.get(f"http://{self.database_address}/status", timeout=0.1)
                if response.status_code == 200:
                    self.database_connected = True
                    self.database_button.setStyleSheet("background-color: #3fb618;\n")
            except (requests.ConnectionError, requests.Timeout):
                self.database_connected = False
                self.database_button.setStyleSheet("background-color: #ff0039;\n")
        threading.Thread(target=check, daemon=True).start()

    # reciving video stream
    def InitReceivingVideoThread(self):
        self.receive_thread = ReceiveVideo()
        self.receive_thread.update_frame.connect(self.update_image)
        self.receive_thread.start()

    def InitReceivingImgThread(self):
        self.receive_lp = QTimer()
        self.receive_lp.timeout.connect(self.update_image_lp)
        self.receive_lp.start(1000)

    def InitReceivingDataThread(self):
        self.receive_data = QTimer()
        self.receive_data.timeout.connect(self.update_data)
        self.receive_data.start(1000)

    #on switch page methods
    def stop_streaming(self):
        if self.streaming_active == True:
            self.receive_thread.stop()
            self.streaming_active = False

    def stop_receiving_license_plate(self):
        if self.receiving_license_plate_active == True:
            self.receive_lp.stop()
            self.receiving_license_plate_active = False

    def stop_receiving_data(self):
        if self.receiving_lp_data_active == True:
            self.receive_data.stop()
            self.receiving_lp_data_active = False

    def clear_table(self):
        self.CarsTable.setRowCount(0)
        self.auth_table.setRowCount(0)

    def on_switch(self):
        self.stop_streaming()
        self.stop_receiving_license_plate()
        self.stop_receiving_data()
        self.clear_table()

############################ HOME #############################

    def update_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QImage(frame.data, 640, 480, QImage.Format_RGB888)
        img_scaled = img.scaled(480, 360, QtCore.Qt.KeepAspectRatio)
        self.video.setPixmap(QPixmap.fromImage(img_scaled))

    def update_image_lp(self):
        if self.database_connected:
            if rd.receive_image(self.database_address):
                if os.path.exists("communication/detected.png"):
                    frame = cv2.imread("communication/detected.png")
                    if frame is not None and frame.size > 0:
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
                        img_scaled = img.scaled(260, 65, QtCore.Qt.IgnoreAspectRatio)
                        self.l_plate_img.setPixmap(QPixmap.fromImage(img_scaled))
        else:
            self.l_plate_img.setStyleSheet("background-color: #d4e6f9;\n"
"color: #000000;\n"
"font: 12pt \"Sans Serif Collection\";")
            self.l_plate_img.setText("Server not connetcted")

    def update_data(self):
        if self.database_connected:
            detection_data = rd.receive_detection_data(self.database_address)
            car_exist_error = False
            capacity_full_error = False
            if detection_data[0] == True:
                license_plate = detection_data[1].get("license_plate", "Not detected").strip()
                acceptance = detection_data[1].get("acceptance", False)
                confidence = detection_data[1].get("confidence", 0)
                confidence = round(float(confidence), 2)
                model = detection_data[1].get("model", "model.pt")
                capacity_left = detection_data[1].get("capacity_left", 1000)
                car_exist_error = detection_data[1].get("already_exists", False)
                capacity_full_error = detection_data[1].get("capacity_full", False)

                self.l_plate_text.setText(license_plate)
                if acceptance:
                    self.descript.setText("")
                    self.status_label.setStyleSheet("background-color: #3fb618;\n"
    "font: 12pt \"Sans Serif Collection\";")
                    self.status_label.setText("Access")
                else:
                    self.descript.setText("")
                    self.status_label.setStyleSheet("background-color: #ff0039;\n"
    "font: 12pt \"Sans Serif Collection\";")
                    self.status_label.setText("Denied access")
                    if car_exist_error:
                        self.descript.setText("This car is already parked!")
                    if capacity_full_error:
                        self.descript.setText("Parking is fully occupied!")

                self.conf_label.show()
                self.conf_label.setText(f"   Model confidence: {confidence}")
                self.model_label.show()
                self.model_label.setText(f"   Used model: {model}")
                self.capacity_label.show()
                self.capacity_label.setText(f"   Capacity left: {capacity_left}")
        else:
            self.l_plate_text.setText("Server not connected")
            self.status_label.setStyleSheet("background-color: #d4e6f9;\n"
"font: 12pt \"Sans Serif Collection\";")
            self.status_label.setText("")
            self.conf_label.hide()
            self.model_label.hide()
            self.capacity_label.hide()


    def display_home_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.home_page)
        self.streaming_active = True
        self.InitReceivingVideoThread()
        self.receiving_license_plate_active = True
        self.InitReceivingImgThread()
        self.conf_label.hide()
        self.model_label.hide()
        self.capacity_label.hide()
        self.receiving_data_active = True
        self.InitReceivingDataThread()

############################ CURRENT STATE #############################

    def update_widgets(self):
        if self.database_connected:
            global_vars = rd.read_global_vars(self.database_address)
            if global_vars[0]:
                cars_today = global_vars[1].get("cars_today", "Error")
                currently_parked = global_vars[1].get("currently_parked", "Error")
                self.value1.setText(f"{cars_today}")
                self.value2.setText(f"{currently_parked}")
                total_capacity = st.settings.get("car_park_info_settings", {}).get("total_capacity", 0)
                self.value3.setText(f"{round((currently_parked / total_capacity), 2)}%")
            else:
                self.value1.setText("No data")
                self.value2.setText("No data")
                self.value3.setText("No data")
        else:
            self.value1.setText("Server error")
            self.value2.setText("Server error")
            self.value3.setText("Server error")


    def update_table(self):
        if self.database_connected:
            self.not_connected_1.hide()
            self.CarsTable.show()
            self.CarsTable.setRowCount(0)
            records_exist, cars_list = rd.get_cars(self.database_address)
            if records_exist == True:
                cars_list_len = len(cars_list)
                print(cars_list_len)

                self.CarsTable.setRowCount(cars_list_len)

                for i in range(0, cars_list_len):
                    self.CarsTable.insertRow(i)
                    self.CarsTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(cars_list[i]['license_plate'])))
                    self.CarsTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(cars_list[i]['entry_time'])))
                    self.CarsTable.setItem(i, 2, QtWidgets.QTableWidgetItem(str(cars_list[i]['entry_time'])))
                    self.CarsTable.setItem(i, 3, QtWidgets.QTableWidgetItem("5 zl"))

                    exit_button = QPushButton("Delete")
                    exit_button.clicked.connect(lambda _, row=i: self.exit_car(row))

                    self.CarsTable.setCellWidget(i, 4, exit_button)
        else:
            self.CarsTable.hide()
            self.not_connected_1.show()
    
    def exit_car(self, row):
        license_plate = self.CarsTable.item(row, 0).text()

        if wtd.delete_car(self.database_address, license_plate):
            self.update_table()

            self.auth_table.removeRow(row)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Exit")
            msg_box.setText("Car took off")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Exit")
            msg_box.setText("Car is stucked at your parking lot")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()


    def display_current_state_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.current_state_page)
        self.update_table()
        self.update_widgets()

############################ AUTH #############################

    def on_auth_submit(self):
        if self.database_connected:
            license_plate = self.lineEdit.text()
            start_qdate = self.dateEdit.date()
            end_qdate = self.dateEdit_2.date()

            start_date = datetime.combine(start_qdate.toPyDate(), datetime.min.time())
            end_date = datetime.combine(end_qdate.toPyDate(), datetime.min.time())

            now = datetime.now()

            if start_date >= now and end_date >= start_date:
                if wtd.insert_authorization(self.database_address, license_plate, start_date.strftime('%Y-%m-%d %H:%M:%S'), end_date.strftime('%Y-%m-%d %H:%M:%S')):
                    msg_box = QtWidgets.QMessageBox()
                    msg_box.setIcon(QtWidgets.QMessageBox.Information)
                    msg_box.setWindowTitle("Data Submitted")
                    msg_box.setText("Data written successfully!")
                    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msg_box.exec_()
                else:
                    msg_box = QtWidgets.QMessageBox()
                    msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                    msg_box.setWindowTitle("Error")
                    msg_box.setText("Failed to write data! Check the server.")
                    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msg_box.exec_()
            else:
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Error")
                msg_box.setText("Check dates and try again!")
                msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg_box.exec_()

            self.auth_table.setRowCount(0)
            self.update_auth_table()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText("Failed to write data! Check the server.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def update_auth_table(self):
        if self.database_connected:
            self.auth_table.show()
            self.not_connected_2.hide()
            records_exist, cars_list = rd.get_auth_cars(self.database_address)

            if records_exist == True:
                cars_list_len = len(cars_list)

                self.auth_table.setRowCount(cars_list_len)

                for i in range(0, cars_list_len):
                    self.auth_table.insertRow(i)
                    
                    self.auth_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(cars_list[i]["license_plate"])))
                    self.auth_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(cars_list[i]["authorization_start_date"])))
                    self.auth_table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(cars_list[i]["authorization_end_date"])))

                    delete_button = QPushButton("Delete")
                    delete_button.clicked.connect(lambda _, row=i: self.delete_auth_car(row))

                    self.auth_table.setCellWidget(i, 3, delete_button)
        else:
            self.auth_table.hide()
            self.not_connected_2.show()

    def delete_auth_car(self, row):
        license_plate = self.auth_table.item(row, 0).text()

        if wtd.delete_authorization(self.database_address, license_plate):
            self.auth_table.removeRow(row)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Delete")
            msg_box.setText("Car authorization removed!")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Delete")
            msg_box.setText("Car ramoving failed! Try again.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def display_auth_list_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.auth_list_page)
        self.update_auth_table()

        if not self.auth_submit_connected:
            self.authSubmit.clicked.connect(self.on_auth_submit)
            self.auth_submit_connected = True

############################ ANALITICS PAGE #######################
    def display_analitics_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.analitics_page)


############################ GPIO PAGE ############################
    def update_gpio_state(self):
        with open('settings/gpio.json', 'r') as f:
            gpio = json.load(f)

        self.input1_type.setCurrentText(gpio["inputs"][0])
        self.input2_type.setCurrentText(gpio["inputs"][1])
        self.input3_type.setCurrentText(gpio["inputs"][2])
        self.input4_type.setCurrentText(gpio["inputs"][3])
        self.input5_type.setCurrentText(gpio["inputs"][4])
        self.input6_type.setCurrentText(gpio["inputs"][5])


        self.output1_type.setCurrentText(gpio["outputs"][0])
        self.output2_type.setCurrentText(gpio["outputs"][1])
        self.output3_type.setCurrentText(gpio["outputs"][2])
        self.output4_type.setCurrentText(gpio["outputs"][3])
        self.output5_type.setCurrentText(gpio["outputs"][4])
        self.output6_type.setCurrentText(gpio["outputs"][5])
            

    def on_save_input_button(self, input_index):
        input_types = {
            1: self.input1_type,
            2: self.input2_type,
            3: self.input3_type,
            4: self.input4_type,
            5: self.input5_type,
            6: self.input6_type
        }

        with open('settings/gpio.json', 'r') as f:
            gpio = json.load(f)

        gpio_input= gpio.get("inputs", [" - "] * 6)
        gpio_input[input_index - 1] = input_types.get(input_index).currentText()

        gpio["inputs"] = gpio_input
        with open("settings/gpio.json", 'w') as f:
            json.dump(gpio, f, indent=4)

        if wtd.change_gpio(self.database_address ,gpio) == True:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Settings")
            msg_box.setText("Settings loaded to module successfully!")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Delete")
            msg_box.setText("Failed to load settings to the module.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def on_save_output_button(self, output_index):
        output_types = {
            1: self.output1_type,
            2: self.output2_type,
            3: self.output3_type,
            4: self.output4_type,
            5: self.output5_type,
            6: self.output6_type
        }

        with open('settings/gpio.json', 'r') as f:
            gpio = json.load(f)

        gpio_output = gpio.get("outputs", [" - "] * 6)
        gpio_output[output_index - 1] = output_types.get(output_index).currentText()

        gpio["outputs"] = gpio_output
        with open("settings/gpio.json", 'w') as f:
            json.dump(gpio, f, indent=4)

        if wtd.change_gpio(self.database_address ,gpio) == True:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Settings")
            msg_box.setText("Settings loaded to module successfully!")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Delete")
            msg_box.setText("Failed to load settings to the module.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
        

    def display_gpio_page(self): 
        self.on_switch()
        self.content.setCurrentWidget(self.gpio_page)
        self.update_gpio_state()
        self.input1_button.clicked.connect(partial(self.on_save_input_button, 1))
        self.input2_button.clicked.connect(partial(self.on_save_input_button, 2))
        self.input3_button.clicked.connect(partial(self.on_save_input_button, 3))
        self.input4_button.clicked.connect(partial(self.on_save_input_button, 4))
        self.input5_button.clicked.connect(partial(self.on_save_input_button, 5))
        self.input6_button.clicked.connect(partial(self.on_save_input_button, 6))
        self.output1_button.clicked.connect(partial(self.on_save_output_button, 1))
        self.output2_button.clicked.connect(partial(self.on_save_output_button, 2))
        self.output3_button.clicked.connect(partial(self.on_save_output_button, 3))
        self.output4_button.clicked.connect(partial(self.on_save_output_button, 4))
        self.output5_button.clicked.connect(partial(self.on_save_output_button, 5))
        self.output6_button.clicked.connect(partial(self.on_save_output_button, 6))

############################ SETTINGS #############################

    def update_settings(self):
        management_settings = st.settings.get("management_settings", {})

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

        connection_settings = st.settings.get("connection_settings", {})
        
        video_ip = connection_settings.get("video", {}).get("ip", "0.0.0.0")
        video_port = connection_settings.get("video", {}).get("port", 0)
        self.video_ip.setText(video_ip)
        self.video_port.setText(str(video_port))

        database_ip = connection_settings.get("database", {}).get("ip", "0.0.0.0")
        database_port = connection_settings.get("database", {}).get("port", 0)
        self.database_ip.setText(database_ip)
        self.database_port.setText(str(database_port))

        recognition_settings = st.settings.get("recognition_settings", {})
        recognition_confidence = recognition_settings.get("recognition_confidence", 50)
        detection_interval = recognition_settings.get("detection_interval", 4)
        recognition_model = recognition_settings.get("recognition_model", "best.pt")
        
        index = self.recognition_model.findText(recognition_model)
        if index != -1:
            self.recognition_model.setCurrentIndex(index)

        region_mode = recognition_settings.get("region_mode", "free")
        if region_mode == 0:
            self.europe.setChecked(True)
        elif region_mode == 1:
            self.north_america.setChecked(True)
        elif region_mode == 2:
            self.asia.setChecked(True)

        self.conf_box.setValue(recognition_confidence)
        self.detection_interval.setValue(fee_per_hour_val)

        car_park_info_settings = st.settings.get("car_park_info_settings", {})
        start_time = car_park_info_settings.get("opening_hour", "08:00")
        close_time = car_park_info_settings.get("closing_hour", "20:00")
        self.openup_time.setTime(QTime.fromString(start_time, "HH:mm:ss"))
        self.close_time.setTime(QTime.fromString(close_time, "HH:mm:ss"))

        capacity = car_park_info_settings.get("total_capacity", 1000)
        self.capacity.setValue(capacity)

    def on_submit_button(self):
        if hasattr(self, "_is_processing") and self._is_processing:
            return  # Prevents duplicate calls
        self._is_processing = True  # Set processing flag

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


        connection_settings.setdefault("database", {})
        connection_settings["database"]["ip"] = self.database_ip.text()
        connection_settings["database"]["port"] = self.database_port.text()

        recognition_settings = {}
        recognition_settings["recognition_confidence"] = self.conf_box.value()
        recognition_settings["detection_interval"] = self.detection_interval.value()
        recognition_settings["recognition_model"] = self.recognition_model.currentText()
        if self.europe.isChecked():
            recognition_settings["region_mode"] = 0
        elif self.north_america.isChecked():
            recognition_settings["region_mode"] = 1
        elif self.asia.isChecked():
            recognition_settings["region_mode"] = 2

        car_park_info_settings = {}
        car_park_info_settings["opening_hour"] = self.openup_time.time().toString("HH:mm:ss")
        car_park_info_settings["closing_hour"] = self.close_time.time().toString("HH:mm:ss")
        car_park_info_settings["total_capacity"] = self.capacity.value()

        st.settings["management_settings"] = management_settings
        st.settings["connection_settings"] = connection_settings
        st.settings["recognition_settings"] = recognition_settings
        st.settings["car_park_info_settings"] = car_park_info_settings

        with open("settings/settings.json", 'w') as f:
            json.dump(st.settings, f, indent=4)

        module_settings = {
            "mode": management_settings["entrance_mode"],
            "payment_mode": management_settings["payment_mode"],
            "recognition_confidence": recognition_settings["recognition_confidence"],
            "detection_interval": recognition_settings["detection_interval"],
            "recognition_model": recognition_settings["recognition_model"],
            "region": recognition_settings["region_mode"],
            "total_capacity": car_park_info_settings["total_capacity"]
        }
        
        self.database_address = f'{st.settings["connection_settings"]["database"]["ip"]}:{st.settings["connection_settings"]["database"]["port"]}'
        self.database_button.setText(self.database_address)
        self.check_server()
        time.sleep(0.15)

        if self.database_connected:
            if wtd.change_settings(self.database_address, module_settings) == True:
                self.synchronization_warning.hide()
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Settings")
                msg_box.setText("Settings loaded to module successfully!")
                msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg_box.exec_()
            else:
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("Delete")
                msg_box.setText("Failed to load settings to the module.")
                msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Settings")
            msg_box.setText("Settings submited successfully!")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
            self.synchronization_warning.show()
        time.sleep(1)
        self._is_processing = False

            
    def on_reset_button(self):
        with open('settings/default_settings.json', 'r') as f:
            default_settings = json.load(f)

        st.settings = default_settings

        with open('settings/settings.json', 'w') as f:
            json.dump(st.settings, f, indent=4)

        self.update_settings()

    def display_settings_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.settings_page)
        self.update_settings()
        self.reset_button.clicked.connect(self.on_reset_button)
        self.submit_button.clicked.connect(self.on_submit_button)

    def handle_refresh(self):
        if self.content.currentWidget() == self.home_page:
            pass
        if self.content.currentWidget() == self.current_state_page:
            self.update_widgets()
            self.update_table()

        if self.content.currentWidget() == self.analitics_page:
            pass
        if self.content.currentWidget() == self.gpio_page:
            pass
        if self.content.currentWidget() == self.settings_page:
            pass
        if self.content.currentWidget() == self.auth_list_page:
            pass

    
    def closeEvent(self, event):
        self.receive_thread.stop()
        event.accept()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())