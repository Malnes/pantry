import os
import json
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
DATA_FILE = "pantry_data.json"

def get_data_file_path(hass: HomeAssistant):
    return hass.config.path(DATA_FILE)

def load_data(hass: HomeAssistant):
    file_path = get_data_file_path(hass)
    if not os.path.exists(file_path):
        data = {"items": []}
        save_data(hass, data)
    else:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            _LOGGER.error("Error loading pantry data: %s", e)
            data = {"items": []}
    return data

def save_data(hass: HomeAssistant, data):
    file_path = get_data_file_path(hass)
    with open(file_path, "w") as f:
        json.dump(data, f)
