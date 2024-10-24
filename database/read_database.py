import requests
from datetime import date

server_address = "192.168.1.133:5000"

def get_cars():
    url = f"http://{server_address}/get_cars"
    response = requests.get(url)

    if response.status_code == 200:
        cars = response.json()
        return [True, cars]
    else:
        error_message = response.json()["message"]
        return [False, error_message]

def get_auth_cars():
    url = f"http://{server_address}/get_authorized_cars"
    response = requests.get(url)

    if response.status_code == 200:
        cars = response.json()
        return [True, cars]
    else:
        error_message = response.json()["message"]
        return [False, error_message]

if __name__ == '__main__':
    print(get_cars())