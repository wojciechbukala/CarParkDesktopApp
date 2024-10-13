import cv2
import numpy as np
import socket
import struct
import pickle
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread

def create_none_img():
    none_img = np.zeros(shape=(80, 280, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(none_img, text='No license plate detected', org=(5, 120), fontFace=font,
                fontScale=0.5, color=(255, 255, 255), thickness=3, lineType=cv2.LINE_AA)

    return none_img

class Receive_License_Plate(QThread):
    update_license_plate = pyqtSignal(np.ndarray)

    def __init__(self, host='192.168.1.133', port=9998):
        super().__init__()
        self.host = host
        self.port = port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

        self.none_img = create_none_img()

    def receive_license_plate(self):
        try:
            data_header = self.client_socket.recv(8)

            data_size = struct.unpack("Q", data_header)[0]

            data = b""
            while len(data) < data_size:
                received_packet = self.client_socket.recv(4 * 1024)
                if not received_packet:
                    self.update_license_plate.emit(self.none_img)
                data += received_packet

            img = pickle.loads(data)
            self.update_license_plate.emit(img)
            #cv2.imwrite("received_license_plate.png", img) 

            return True

        except Exception as e:
            self.update_license_plate.emit(self.none_img)
            return False

    def stop(self):
        self.client_socket.close()

if __name__ == "__main__":
    receiver = Receive_License_Plate(host='192.168.1.133', port=9998)
    try:
        while receiver.receive_license_plate():
            pass
    finally:
        receiver.stop()
