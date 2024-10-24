import socket
import struct
import time
import threading
import json
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QThread

class ReceiveData(QThread):

    license_plate_string = pyqtSignal(str)

    def __init__(self, host='0.0.0.0', port=9997):
        super().__init__()
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False


    def connect(self):
        if self.client_socket is None:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                #print("[INFO] Połączono z serwerem.")
            except Exception as e:
                pass

    def receive_data(self):
        if self.client_socket:
            try:
                data_header = self.client_socket.recv(8)

                if not data_header:
                    #print("[ERROR] Połączenie z serwerem zostało zamknięte.")
                    self.client_socket.close()
                    self.client_socket = None
                    return

                data_size = struct.unpack("Q", data_header)[0]

                data = b""
                while len(data) < data_size:
                    received_packet = self.client_socket.recv(4 * 1024)
                    if not received_packet: 
                        #print("[ERROR] Połączenie z serwerem zostało zamknięte.")
                        self.client_socket.close()
                        self.client_socket = None
                        return
                    data += received_packet

                received_data = json.loads(data.decode('utf-8'))

                plate = received_data.get('license_plate', 'No plate detected')
                self.license_plate_string.emit(plate)


            except Exception as e:
                self.client_socket.close()
                self.client_socket = None

    def run(self):
        self.running = True
        while self.running:
            self.connect() 
            self.receive_data()
            time.sleep(1)

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":
    receiver = ReceiveData(host='192.168.1.133', port=9997)

    thread = threading.Thread(target=receiver.run)
    thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        receiver.stop()
        thread.join()
