import json

settings = {}

def read_settings():
    with open('settings/settings.json', 'r') as f:
        loaded_settings = json.load(f)
    global settings
    settings = loaded_settings

