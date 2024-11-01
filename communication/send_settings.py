import requests

# server_address = "192.168.8.118:5000"

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
    pass