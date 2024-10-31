import requests
import cv2
import numpy as np

server_address = "192.168.8.118:5000"

def receive_detection_data():
    url = f"http://{server_address}/send_detection_data"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return [True, data]
    else:
        error_message = response.json()["message"]
        return [False, error_message]