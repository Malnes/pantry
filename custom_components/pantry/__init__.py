import logging
import voluptuous as vol
from datetime import datetime
from homeassistant.core import ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import HomeAssistantType

DOMAIN = "pantry"
STORAGE_KEY = "pantry"
STORAGE_VERSION = 1

_LOGGER = logging.getLogger(__name__)

ITEM_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("quantity"): vol.All(int, vol.Range(min=0)),
    vol.Required("min_quantity"): vol.All(int, vol.Range(min=0)),
    vol.Required("expiration_dates"): [cv.date]
})

async def async_setup(hass: HomeAssistantType, config: dict):
    """Set up the Pantry component."""
    hass.data.setdefault(DOMAIN, {})
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    
    # Load data
    data = await store.async_load() or {"items": []}
    hass.data[DOMAIN] = {
        "store": store,
        "items": data.get("items", [])
    }

    # Register services
    async def handle_add_item(call: ServiceCall):
        """Add new item to pantry."""
        item = {
            "name": call.data["name"],
            "quantity": call.data["quantity"],
            "min_quantity": call.data["min_quantity"],
            "expiration_dates": call.data.get("expiration_dates", [])
        }
        hass.data[DOMAIN]["items"].append(item)
        await hass.data[DOMAIN]["store"].async_save({"items": hass.data[DOMAIN]["items"]})

    async def handle_update_item(call: ServiceCall):
        """Update existing item."""
        item_id = call.data["item_id"]
        new_data = call.data["item"]
        hass.data[DOMAIN]["items"][item_id].update(new_data)
        await hass.data[DOMAIN]["store"].async_save({"items": hass.data[DOMAIN]["items"]})

    async def handle_delete_item(call: ServiceCall):
        """Delete item by index."""
        del hass.data[DOMAIN]["items"][call.data["item_id"]]
        await hass.data[DOMAIN]["store"].async_save({"items": hass.data[DOMAIN]["items"]})

    hass.services.async_register(
        DOMAIN, "add_item", handle_add_item, schema=ITEM_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, "update_item", handle_update_item,
        schema=vol.Schema({
            vol.Required("item_id"): int,
            vol.Required("item"): ITEM_SCHEMA
        })
    )
    hass.services.async_register(
        DOMAIN, "delete_item", handle_delete_item,
        schema=vol.Schema({vol.Required("item_id"): int})
    )

# Register websocket API
    hass.components.websocket_api.async_register_command(
        'pantry/get_items',
        websocket_get_items,
        websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend({
            vol.Required('type'): 'pantry/get_items'
        })
    )
    
    return True

@websocket_api.async_response
async def websocket_get_items(
    hass: HomeAssistantType,
    connection: websocket_api.ActiveConnection,
    msg: dict
):
    """Return all items through websocket."""
    items = hass.data[DOMAIN]["items"]
    connection.send_message(websocket_api.result_message(
        msg['id'], {'items': items}
    ))