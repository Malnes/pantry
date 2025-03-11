import logging
import os
import json
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

DOMAIN = "food_stockpile"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the food_stockpile integration."""
    # Create data file if it doesn't exist
    data_file_path = hass.config.path(f"{DOMAIN}_data.json")
    if not os.path.exists(data_file_path):
        with open(data_file_path, "w") as f:
            json.dump([], f, indent=2)

    hass.data[DOMAIN] = {
        "data_file": data_file_path,
        "items": []
    }

    # Load items from JSON file
    await load_items(hass)

    # Register services
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

    # Setup sensor platform
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )

    # Register the custom panel (iframe approach)
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


async def load_items(hass):
    """Load items from JSON file into hass.data."""
    data_file_path = hass.data[DOMAIN]["data_file"]
    try:
        with open(data_file_path, "r") as f:
            hass.data[DOMAIN]["items"] = json.load(f)
    except Exception as e:
        _LOGGER.error("Error loading food stockpile data: %s", e)
        hass.data[DOMAIN]["items"] = []


async def save_items(hass):
    """Save current items to JSON file."""
    data_file_path = hass.data[DOMAIN]["data_file"]
    with open(data_file_path, "w") as f:
        json.dump(hass.data[DOMAIN]["items"], f, indent=2)


async def add_item(hass, item_name, quantity, expiration_dates):
    """Add or update items in the data store."""
    items = hass.data[DOMAIN]["items"]
    # Check if item already exists
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        # Update quantity
        existing_item["current_quantity"] += quantity
        # Add new expiration dates
        existing_item["expiration_dates"].extend(expiration_dates)
    else:
        # Create new
        items.append({
            "item": item_name,
            "current_quantity": quantity,
            "min_quantity": 1,  # default minimal
            "expiration_dates": expiration_dates
        })

    await save_items(hass)
    # Update sensor
    await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")


async def edit_item(hass, item_name, min_quantity):
    """Edit min_quantity for an existing item."""
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        existing_item["min_quantity"] = min_quantity
        await save_items(hass)
        await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")


async def remove_item(hass, item_name, quantity, expiration_dates):
    """Remove or reduce items from the data store."""
    items = hass.data[DOMAIN]["items"]
    existing_item = next((i for i in items if i["item"].lower() == item_name.lower()), None)
    if existing_item:
        # Decrease quantity
        existing_item["current_quantity"] -= quantity
        if existing_item["current_quantity"] < 0:
            existing_item["current_quantity"] = 0
        
        # If specific expiration dates provided, remove them
        for exp_date in expiration_dates:
            if exp_date in existing_item["expiration_dates"]:
                existing_item["expiration_dates"].remove(exp_date)

        # If quantity is zero and no expiration dates left, you might remove item entirely
        # But we’ll keep it in the list so it doesn't vanish from sensor until user explicitly removes it.
        await save_items(hass)
        await hass.helpers.entity_component.async_update_entity(f"sensor.{DOMAIN}")
