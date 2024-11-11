import requests
import cv2
import numpy as np
import settings.handle_settings as st


def receive_detection_data(server_address):
    url = f"http://{server_address}/send_detection_data"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return [True, data]
    else:
        return [False, "error"]
