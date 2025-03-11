import os
import json
import logging

from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .views import PantryDataView
from .sensor import PantrySensor

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
        except Exception:
            data = {"items": []}
    return data

def save_data(hass: HomeAssistant, data):
    file_path = get_data_file_path(hass)
    with open(file_path, "w") as f:
        json.dump(data, f)

async def async_setup_entry(hass: HomeAssistant, entry):
    # Register HTTP view for CRUD operations
    hass.http.register_view(PantryDataView)
    # Register the static path for the frontend panel files
    panel_path = os.path.join(os.path.dirname(__file__), "frontend")
    hass.http.register_static_path("/pantry", panel_path, False)
    # Register a built-in panel accessible from the sidebar (iframe style)
    hass.components.frontend.async_register_built_in_panel(
        component_name="iframe",
        sidebar_title="Pantry",
        sidebar_icon="mdi:food",
        frontend_url_path="pantry",
        config={"url": "/pantry/index.html"}
    )
    # Set up a single sensor entity that holds all pantry items
    hass.data.setdefault(DOMAIN, {})
    sensor = PantrySensor(load_data(hass))
    hass.data[DOMAIN]["sensor"] = sensor
    hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, entry)
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return True
