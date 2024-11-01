import requests
import cv2
import numpy as np

server_address = "192.168.8.118:5000"

def error_img(description):
    none_img = np.zeros(shape=(80, 280, 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    cv2.putText(none_img, text=description, org=(90, 40), fontFace=font,
                fontScale=0.5, color=(255, 255, 255), thickness=1, lineType=cv2.LINE_AA)

    cv2.imwrite("communication/detected.png", none_img)

def receive_image(server_address):
    url = f"http://{server_address}/send_detection_img"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open("communication/detected.png", 'wb') as file:
            file.write(response.content)
        return True
    else:
        return False