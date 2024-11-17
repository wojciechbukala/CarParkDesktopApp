import requests
from datetime import date

#server_address = "192.168.8.118:5000"

def get_cars(server_address):
    url = f"http://{server_address}/get_cars"
    response = requests.get(url)

    if response.status_code == 200:
        cars = response.json()
        return [True, cars]
    else:
        error_message = response.json()["message"]
        return [False, error_message]

def get_auth_cars(server_address):
    url = f"http://{server_address}/get_authorized_cars"
    response = requests.get(url)

    if response.status_code == 200:
        cars = response.json()
        return [True, cars]
    else:
        error_message = response.json()["message"]
        return [False, error_message]

def receive_detection_data(server_address):
    url = f"http://{server_address}/send_detection_data"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return [True, data]
    else:
        return [False, "error"]


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
        with open("database/detected.png", 'wb') as file:
            file.write(response.content)
        return True
    else:
        return False

def read_global_vars(server_address):
    url = f"http://{server_address}/send_global_vars"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        data = response.json()
        return [True, data]
    else:
        return [False, "error"]

def get_gate_state(server_address):
    url = f"http://{server_address}/gate_state"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        data = response.json()
        return [True, data]
    else:
        return [False, "error"]

if __name__ == '__main__':
    print(get_cars())