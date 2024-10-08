import sys
import cv2
import numpy as np
import socket
import struct
import time
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread

def create_no_signal_img():
    no_signal_frame = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(no_signal_frame, text='No signal detected', org=(90, 230), fontFace=font,
    fontScale=1.5, color=(255,255,255), thickness=3, lineType=cv2.LINE_AA)

    cv2.putText(no_signal_frame, text='Check camera. Contact maintenance if problem continious', org=(10, 270), fontFace=font,
    fontScale=0.65, color=(255,255,255), thickness=2, lineType=cv2.LINE_AA)

    return no_signal_frame


class Receive(QThread):
    update_frame = pyqtSignal(np.ndarray)

    def __init__(self, host='0.0.0.0', port=9999, bufSize=20000):
        super().__init__()
        self.host = host
        self.port = port
        self.bufSize = bufSize
        self.server_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_client.bind((self.host, self.port))
        self.server_client.settimeout(0.5)
        self.running = True
        self.no_signal_frame = create_no_signal_img()

    def run(self):
        while self.running:
            try:
                data, address = self.server_client.recvfrom(4)
                length = struct.unpack('i', data)[0]

                frame_data = b''
                while len(frame_data) < length:
                    packet, address = self.server_client.recvfrom(self.bufSize)
                    frame_data += packet

                frame = np.frombuffer(frame_data, dtype=np.uint8)
                img = cv2.imdecode(frame, cv2.IMREAD_COLOR)

                if img is not None:
                    self.update_frame.emit(img)

                time.sleep(0.01)

            except socket.timeout:
                self.update_frame.emit(self.no_signal_frame)
                continue

            except socket.error as e:
                print("Socket error, restarting...")
                time.sleep(0.01)

        self.server_client.close()

    def stop(self):
        self.running = False
        self.wait()