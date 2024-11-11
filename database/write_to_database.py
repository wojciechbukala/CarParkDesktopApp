import requests
from datetime import date

#server_address = "192.168.8.118:5000"

def delete_car(server_address, license_plate):
    delete = {
        "license_plate": f"{license_plate}"
    }

    url = f"http://{server_address}/delete_car"
    response = requests.post(url, json=delete)

    if response.status_code == 201:
        return True
    else:
        return False

def insert_authorization(server_address, license_plate, start_date, end_date):
    authorization = {
        "license_plate": f"{license_plate}",
        "start_date": f"{start_date}",
        "end_date": f"{end_date}"
    }

    url = f"http://{server_address}/add_authorization"
    response = requests.post(url, json=authorization)

    if response.status_code == 201:
        return True
    else:
        return False

def delete_authorization(server_address, license_plate):
    delete = {
        "license_plate": f"{license_plate}"
    }

    url = f"http://{server_address}/delete_authorization"
    response = requests.post(url, json=delete)

    if response.status_code == 201:
        return True
    else:
        return False

def change_settings(server_address, settings_dict):
    url = f"http://{server_address}/change_settings"
    response = requests.post(url, json=settings_dict)

    if response.status_code == 200:
        return True
    else:
        return False

def change_inputs(server_address, inputs):
    url = f"http://{server_address}/change_inputs"
    response = requests.post(url, json=inputs)

    if response.status_code == 200:
        return True
    else:
        return False


if __name__ == '__main__':
    delete_authorization("ZS12345")