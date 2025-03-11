import logging
import os
import json

from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

from homeassistant.components.http.static import StaticPathConfig
from homeassistant.components.frontend import async_register_built_in_panel

# If you keep a separate const.py:
# from .const import DOMAIN
DOMAIN = "food_stockpile"

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """
    Called by Home Assistant to set up this integration (no config flow).
    We handle everything here: data file creation, service registration, sensor, panel, etc.
    """
    # Path to the JSON file that stores your items
    data_file_path = hass.config.path(f"{DOMAIN}_data.json")
    if not os.path.exists(data_file_path):
        with open(data_file_path, "w") as f:
            json.dump([], f, indent=2)

    # Keep domain-specific data in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        "data_file": data_file_path,
        "items": []
    }

    # Load items from the JSON file
    await load_items(hass)

    # Register our custom services
    async def async_add_item(call):
        """Add or update items."""
        item_name = call.data.get("item_name")
        quantity = call.data.get("quantity", 1)
        expiration_dates = call.data.get("expiration_dates", [])
        await add_item(hass, item_name, quantity, expiration_dates)

    async def async_edit_item(call):
        """Edit min_quantity for an existing item."""
        item_name = call.data.get("item_name")
        min_quantity = call.data.get("min_quantity")
        await edit_item(hass, item_name, min_quantity)

    async def async_remove_item(call):
        """Remove or reduce items."""
        item_name = call.data.get("item_name")
        quantity = call.data.get("quantity", 1)
        expiration_dates = call.data.get("expiration_dates", [])
        await remove_item(hass, item_name, quantity, expiration_dates)

    hass.services.async_register(DOMAIN, "add_item", async_add_item)
    hass.services.async_register(DOMAIN, "edit_item", async_edit_item)
    hass.services.async_register(DOMAIN, "remove_item", async_remove_item)

    # Set up sensor platform (the sensor is defined in sensor.py)
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    # Register the static panel folder (avoid deprecated call)
    panel_path = os.path.join(os.path.dirname(__file__), "panel")
    await hass.http.async_register_static_paths([
        StaticPathConfig("/food_stockpile_panel", panel_path, True)
    ])

    # Register as a built-in panel
    await async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title="Food Stockpile",
        sidebar_icon="mdi:food",
        frontend_url_path="food_stockpile_panel",
        config={"url": "/food_stockpile_panel/index.html"},
    )

    return True

async def load_items(hass: HomeAssistant):
    """Load items from the JSON file into hass.data."""
    data_file_path = hass.data[DOMAIN]["data_file"]
    try:
        with open(data_file_path, "r") as f:
            hass.data[DOMAIN]["items"] = json.load(f)
    except Exception as e:
        _LOGGER.error("Error loading food stockpile data: %s", e)
        hass.data[DOMAIN]["items"] = []

async def save_items(hass: HomeAssistant):
    """Save items to the JSON file."""
    data_file_path = hass.data[DOMAIN]["data_file"]
    with open(data_file_path, "w") as f:
        json.dump(hass.data[DOMAIN]["items"], f, indent=2)

async def add_item(hass: HomeAssistant, item_name: str, quantity: int, expiration_dates: list):
    """Add or update an item."""
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["current_quantity"] += quantity
        existing_item["expiration_dates"].extend(expiration_dates)
    else:
        items.append({
            "item": item_name,
            "current_quantity": quantity,
            "min_quantity": 1,  # default minimum
            "expiration_dates": expiration_dates
        })

    await save_items(hass)
    await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")

async def edit_item(hass: HomeAssistant, item_name: str, min_quantity: int):
    """Edit the minimum quantity of an existing item."""
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["min_quantity"] = min_quantity
        await save_items(hass)
        await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")

async def remove_item(hass: HomeAssistant, item_name: str, quantity: int, expiration_dates: list):
    """Remove or reduce an item."""
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["current_quantity"] = max(0, existing_item["current_quantity"] - quantity)

        # If specific expiration dates given, remove them from the list
        for exp in expiration_dates:
            if exp in existing_item["expiration_dates"]:
                existing_item["expiration_dates"].remove(exp)

        await save_items(hass)
        await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")
