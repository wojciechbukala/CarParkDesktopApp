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
        self.history_button.clicked.connect(self.display_history_page)
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

        self.output1_type.addItem(" - ")
        self.output1_type.addItem("recognition: impulse")
        self.output1_type.addItem("recognition: high for 10 seconds")
        self.output1_type.addItem("car passed input: impulse")
        self.output1_type.addItem("recog & car passed input: impulse")

        self.output2_type.addItem(" - ")
        self.output2_type.addItem("recognition: impulse")
        self.output2_type.addItem("recognition: high for 10 seconds")
        self.output2_type.addItem("car passed input: impulse")
        self.output2_type.addItem("recog & car passed input: impulse")
                
        self.output3_type.addItem(" - ")
        self.output3_type.addItem("recognition: impulse")
        self.output3_type.addItem("recognition: high for 10 seconds")
        self.output3_type.addItem("car passed input: impulse")
        self.output3_type.addItem("recog & car passed input: impulse")

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
            # if self.database_connected:
            #     global_vars = rd.read_global_vars(self.database_address)
            #     if global_vars[0]:
            #         gate_state = global_vars[1].get("gate_state", "Error")
            #         if gate_state == "Error":
            #             self.gate_state_lbl.setText("  GATE: NO DATA  ")
            #         elif gate_state:
            #             self.gate_state_lbl.setText("  GATE: OPEN  ")
            #             self.gate_state_lbl.setStyleSheet("background-color: #3fb618;\n")
            #         else:
            #             self.gate_state_lbl.setText("  GATE: CLOSED  ")
            #             self.gate_state_lbl.setStyleSheet("background-color: #ff0039;\n")
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
        self.receive_data.start(2000)

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
                if os.path.exists("database/detected.png"):
                    frame = cv2.imread("database/detected.png")
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
                capacity_occupied = detection_data[1].get("capacity_occupied", 0)
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
                self.capacity_label.setText(f"   Capacity occupied: {capacity_occupied}")
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
            #global_vars = rd.read_global_vars(self.database_address)
            if rd.get_cars_today(self.database_address)[0]:
                cars_today = rd.get_cars_today(self.database_address)[1].get("cars_today")
                currently_parked = self.CarsTable.rowCount()//2
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
                current_time = datetime.utcnow()

                self.CarsTable.setRowCount(cars_list_len)

                for i in range(0, cars_list_len):
                    self.CarsTable.insertRow(i)
                    self.CarsTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(cars_list[i]['carID'])))
                    self.CarsTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(cars_list[i]['license_plate'])))
                    date_obj = datetime.strptime(str(cars_list[i]['entry_time']), "%a, %d %b %Y %H:%M:%S GMT")
                    duration = current_time - date_obj
                    total_seconds = abs(duration.total_seconds())
                    hours = int(total_seconds // 3600)
                    minutes = 60 - int((total_seconds % 3600) // 60)
                    seconds = 60 - int(total_seconds % 60)
                    self.CarsTable.setItem(i, 2, QtWidgets.QTableWidgetItem(f"{hours:02d}:{minutes:02d}:{seconds:02d}"))
                                        
                    if st.settings["management_settings"]["payment_mode"] == "fee_per_hour":
                        fee = int(st.settings["management_settings"]["fee_per_hour"]) * (hours+1)
                    elif st.settings["management_settings"]["payment_mode"] == "entrance_fee":
                        fee = int(st.settings["management_settings"]["fee_per_hour"])
                    else:
                        fee = 0
                    self.CarsTable.setItem(i, 3, QtWidgets.QTableWidgetItem(f"{fee}zl"))

                    exit_button = QPushButton("Exit")
                    exit_button.clicked.connect(lambda _, row=i: self.exit_car(row))

                    self.CarsTable.setCellWidget(i, 4, exit_button)
        else:
            self.CarsTable.hide()
            self.not_connected_1.show()
    
    def exit_car(self, row):
        car_id = self.CarsTable.item(row, 0).text()

        if wtd.delete_car(self.database_address, car_id):
            self.update_table()
            currently_parked = self.CarsTable.rowCount()//2
            self.value2.setText(f"{currently_parked}")

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
                    start_date_str = str(cars_list[i]["authorization_start_date"])
                    start_date_obj = datetime.strptime(start_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                    formatted_start_date = start_date_obj.strftime("%d.%m.%Y")

                    self.auth_table.setItem(i, 1, QtWidgets.QTableWidgetItem(formatted_start_date))

                    end_date_str = str(cars_list[i]["authorization_end_date"])
                    end_date_obj = datetime.strptime(end_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                    formatted_end_date = end_date_obj.strftime("%d.%m.%Y")
                    self.auth_table.setItem(i, 2, QtWidgets.QTableWidgetItem(formatted_end_date))

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

############################ HISTORY PAGE #######################
    def update_history_table(self):
        if self.database_connected:
            self.ServerNC_lbl.hide()
            self.HistoryTable.show()
            self.HistoryTable.setRowCount(0)
            records_exist, history_list = rd.get_history(self.database_address)
            if records_exist == True:
                history_list_len = len(history_list)

                self.HistoryTable.setRowCount(history_list_len)

                for i in range(0, history_list_len):
                    self.HistoryTable.insertRow(i)
                    self.HistoryTable.setItem(i, 0, QtWidgets.QTableWidgetItem(str(history_list[i]['carID'])))
                    self.HistoryTable.setItem(i, 1, QtWidgets.QTableWidgetItem(str(history_list[i]['license_plate'])))
                    start_date_str = str(history_list[i]["entry_time"])
                    start_date_obj = datetime.strptime(start_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                    formatted_start_date = start_date_obj.strftime("%d.%m.%Y %H:%M")

                    self.HistoryTable.setItem(i, 2, QtWidgets.QTableWidgetItem(formatted_start_date))

                    end_date_str = str(history_list[i]["exit_time"])
                    end_date_obj = datetime.strptime(end_date_str, "%a, %d %b %Y %H:%M:%S GMT")
                    formatted_end_date = end_date_obj.strftime("%d.%m.%Y %H:%M")

                    self.HistoryTable.setItem(i, 3, QtWidgets.QTableWidgetItem(formatted_end_date))

                    duration= end_date_obj - start_date_obj
                    total_seconds = abs(duration.total_seconds())
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = int(total_seconds % 60)

                    self.HistoryTable.setItem(i, 4, QtWidgets.QTableWidgetItem(f"{hours}:{minutes}:{seconds}"))
                    self.HistoryTable.setItem(i, 5, QtWidgets.QTableWidgetItem(str(history_list[i]['payment']['amount'])))

                    exit_button = QPushButton("Remove")
                    exit_button.clicked.connect(lambda _, row=i: self.remove_history(row))

                    self.HistoryTable.setCellWidget(i, 6, exit_button)
        else:
            self.ServerNC_lbl.show()
            self.HistoryTable.hide()
    
    def remove_history(self, row):
        car_id = self.HistoryTable.item(row, 0).text()

        if wtd.remove_history(self.database_address, car_id):
            self.HistoryTable.removeRow(row)
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Exit")
            msg_box.setText("Car took off")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()
            self.update_history_table()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Exit")
            msg_box.setText("Car is stucked at your parking lot")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()



    def display_history_page(self):
        self.on_switch()
        self.content.setCurrentWidget(self.history_page)
        self.update_history_table()


############################ GPIO PAGE ############################
    def update_gpio_state(self):
        with open('settings/gpio.json', 'r') as f:
            gpio = json.load(f)

        self.output1_type.setCurrentText(gpio["outputs"][0])
        self.output2_type.setCurrentText(gpio["outputs"][1])
        self.output3_type.setCurrentText(gpio["outputs"][2])


    def on_save_output_button(self, output_index):
        output_types = {
            1: self.output1_type,
            2: self.output2_type,
            3: self.output3_type,
        }

        with open('settings/gpio.json', 'r') as f:
            gpio = json.load(f)

        gpio_output = gpio.get("outputs", [" - "] * 6)
        gpio_output[output_index - 1] = output_types.get(output_index).currentText()

        gpio["outputs"] = gpio_output
        with open("settings/gpio.json", 'w') as f:
            json.dump(gpio, f, indent=4)

        if self.database_connected:
            if wtd.change_gpio(self.database_address ,gpio) == True:
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("GPIO")
                msg_box.setText("Output loaded to module successfully!")
                msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg_box.exec_()
            else:
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Information)
                msg_box.setWindowTitle("GPIO")
                msg_box.setText("Failed to load output to the module.")
                msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
                msg_box.exec_()
        else:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("GPIO")
            msg_box.setText("Module not connected, output saved localy.")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def display_gpio_page(self): 
        self.on_switch()
        self.content.setCurrentWidget(self.gpio_page)
        self.update_gpio_state()
        self.output1_button.clicked.connect(partial(self.on_save_output_button, 1))
        self.output2_button.clicked.connect(partial(self.on_save_output_button, 2))
        self.output3_button.clicked.connect(partial(self.on_save_output_button, 3))

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
            "fee_per_hour": management_settings["fee_per_hour"],
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

        if self.content.currentWidget() == self.history_page:
            self.update_history_table()
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