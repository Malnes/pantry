import os
import logging

from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .views import PantryDataView
from .sensor import PantrySensor
from .storage import load_data

_LOGGER = logging.getLogger(__name__)

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
