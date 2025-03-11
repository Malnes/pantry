import logging
import os
import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Called when Home Assistant starts up (not used for config flow)."""
    # Return True so HA knows the domain is valid. Actual setup happens in async_setup_entry.
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Food Stockpile from a config entry."""
    data_file_path = hass.config.path(f"{DOMAIN}_data.json")
    if not os.path.exists(data_file_path):
        with open(data_file_path, "w") as f:
            json.dump([], f, indent=2)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {
        "data_file": data_file_path,
        "items": []
    }

    # Load items from file
    await load_items(hass)

    # Register services
    async def async_add_item(call):
        item_name = call.data.get("item_name")
        quantity = call.data.get("quantity", 1)
        expiration_dates = call.data.get("expiration_dates", [])
        await add_item(hass, item_name, quantity, expiration_dates)

    async def async_edit_item(call):
        item_name = call.data.get("item_name")
        min_quantity = call.data.get("min_quantity")
        await edit_item(hass, item_name, min_quantity)

    async def async_remove_item(call):
        item_name = call.data.get("item_name")
        quantity = call.data.get("quantity", 1)
        expiration_dates = call.data.get("expiration_dates", [])
        await remove_item(hass, item_name, quantity, expiration_dates)

    hass.services.async_register(DOMAIN, "add_item", async_add_item)
    hass.services.async_register(DOMAIN, "edit_item", async_edit_item)
    hass.services.async_register(DOMAIN, "remove_item", async_remove_item)

    # Set up sensor platform
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, {})
    )

    # Register panel
    panel_path = os.path.join(os.path.dirname(__file__), "panel")
    hass.http.register_static_path("/food_stockpile_panel", panel_path, True)
    hass.components.frontend.async_register_built_in_panel(
        component_name="iframe",
        sidebar_title="Food Stockpile",
        sidebar_icon="mdi:food",
        frontend_url_path="food_stockpile_panel",
        config={"url": "/food_stockpile_panel/index.html"},
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the config entry (if user removes it)."""
    # Unregister services if you wish
    if hass.services.has_service(DOMAIN, "add_item"):
        hass.services.async_remove(DOMAIN, "add_item")
    if hass.services.has_service(DOMAIN, "edit_item"):
        hass.services.async_remove(DOMAIN, "edit_item")
    if hass.services.has_service(DOMAIN, "remove_item"):
        hass.services.async_remove(DOMAIN, "remove_item")

    # Optionally remove the panel. You might keep it, or do:
    await hass.components.frontend.async_remove_panel("food_stockpile_panel")

    hass.data.pop(DOMAIN, None)
    return True

async def load_items(hass):
    data_file_path = hass.data[DOMAIN]["data_file"]
    try:
        with open(data_file_path, "r") as f:
            hass.data[DOMAIN]["items"] = json.load(f)
    except Exception as e:
        _LOGGER.error("Error loading food stockpile data: %s", e)
        hass.data[DOMAIN]["items"] = []

async def save_items(hass):
    data_file_path = hass.data[DOMAIN]["data_file"]
    with open(data_file_path, "w") as f:
        json.dump(hass.data[DOMAIN]["items"], f, indent=2)

async def add_item(hass, item_name, quantity, expiration_dates):
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["current_quantity"] += quantity
        existing_item["expiration_dates"].extend(expiration_dates)
    else:
        items.append({
            "item": item_name,
            "current_quantity": quantity,
            "min_quantity": 1,
            "expiration_dates": expiration_dates
        })
    await save_items(hass)
    await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")

async def edit_item(hass, item_name, min_quantity):
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["min_quantity"] = min_quantity
        await save_items(hass)
        await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")

async def remove_item(hass, item_name, quantity, expiration_dates):
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["current_quantity"] = max(0, existing_item["current_quantity"] - quantity)
        for exp_date in expiration_dates:
            if exp_date in existing_item["expiration_dates"]:
                existing_item["expiration_dates"].remove(exp_date)
        await save_items(hass)
        await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")
