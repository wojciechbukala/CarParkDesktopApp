import cv2
import numpy as np
import socket
import struct
import pickle
import time
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread

def error_img(description):
    none_img = np.zeros(shape=(80, 280, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(none_img, text=description, org=(90, 40), fontFace=font,
                fontScale=0.5, color=(255, 255, 255), thickness=1, lineType=cv2.LINE_AA)

    return none_img


class ReceiveImg(QThread):

    license_plate = pyqtSignal(np.ndarray)

    def __init__(self, host='0.0.0.0', port=9998):
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False

        self.no_signal_img = error_img("Signal not detected")
        self.no_license_plate_img = error_img("License plate not detected")
        self.current_img = self.no_signal_img
        cv2.imwrite("received_license_plate.png", self.no_signal_img)

    def try_connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            return True
        except Exception as e:
            return False

    def receive_license_plate(self):
        try:
            data_header = self.client_socket.recv(8)  # Odbierz pierwsze 8 bajtów (rozmiar)

            data_size = struct.unpack("Q", data_header)[0]  # Odszyfruj rozmiar wiadomości

            data = b""
            while len(data) < data_size:  # Odbieraj dane aż do uzyskania pełnej wiadomości
                received_packet = self.client_socket.recv(4 * 1024)
                data += received_packet

            img = pickle.loads(data)
            self.current_img = img
            #cv2.imwrite("received_license_plate.png", img)

        except Exception as e:
            self.current_img = self.no_signal_img
            #cv2.imwrite("received_license_plate.png", self.current_img)

    def run(self):
        self.running = True
        while self.running:
            if self.try_connect():
                self.receive_license_plate()
                self.license_plate.emit(self.current_img)
            else:
                self.current_img = self.no_signal_img
                self.license_plate.emit(self.current_img)


    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()

# if __name__ == "__main__":
#     receiver = Receive_License_Plate(host='192.168.1.133', port=9998)

#     thread = threading.Thread(target=receiver.run)
#     thread.start()

#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         receiver.stop()
#         thread.join()
