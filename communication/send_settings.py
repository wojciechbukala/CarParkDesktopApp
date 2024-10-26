import requests

server_address = "192.168.1.133:5000"

def change_settings(settings_dict):
    url = f"http://{server_address}/change_settings"
    response = requests.post(url, json=settings_dict)

    if response.status_code == 200:
        return True
    else:
        return False


if __name__ == '__main__':
    pass