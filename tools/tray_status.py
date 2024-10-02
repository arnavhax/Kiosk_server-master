import json
import os

TRAY_STATUS_FILE = os.path.join('data', 'tray_status.json')


def load_tray_status():
    with open(TRAY_STATUS_FILE, 'r') as f:
        return json.load(f)


def save_tray_status(tray_status):
    with open(TRAY_STATUS_FILE, 'w') as f:
        json.dump(tray_status, f)