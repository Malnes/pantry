import logging
import uuid
from datetime import datetime
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN, ATTR_ITEM_ID, ATTR_NAME, ATTR_QUANTITY,
    ATTR_MIN_QUANTITY, ATTR_EXPIRATIONS, DATA_STORAGE
)
from .storage import PantryStorage

_LOGGER = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"

ITEM_SCHEMA = vol.Schema({
    vol.Required(ATTR_NAME): cv.string,
    vol.Required(ATTR_QUANTITY): vol.Coerce(int),
    vol.Required(ATTR_MIN_QUANTITY): vol.Coerce(int),
    vol.Optional(ATTR_EXPIRATIONS, default=[]): vol.All(
        cv.ensure_list, [cv.date]
    )
})

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Pantry component."""
    storage = PantryStorage(hass)
    hass.data[DOMAIN] = {DATA_STORAGE: storage}
    
    await storage.async_load_data()
    
    # Register services
    async def async_handle_add_item(call: ServiceCall):
        """Add new pantry item."""
        item_data = dict(call.data)
        item_id = str(uuid.uuid4())
        
        # Convert dates to strings
        if ATTR_EXPIRATIONS in item_data:
            item_data[ATTR_EXPIRATIONS] = [
                d.strftime(DATE_FORMAT) for d in item_data[ATTR_EXPIRATIONS]
            ]
        
        storage.data["items"][item_id] = item_data
        await storage.async_save_data()
        return item_id

    async def async_handle_update_item(call: ServiceCall):
        """Update existing item."""
        item_id = call.data[ATTR_ITEM_ID]
        items = storage.data["items"]
        
        if item_id not in items:
            raise ValueError("Item not found")
            
        updated_data = dict(call.data)
        del updated_data[ATTR_ITEM_ID]
        
        # Convert dates to strings if present
        if ATTR_EXPIRATIONS in updated_data:
            updated_data[ATTR_EXPIRATIONS] = [
                d.strftime(DATE_FORMAT) for d in updated_data[ATTR_EXPIRATIONS]
            ]
        
        items[item_id].update(updated_data)
        await storage.async_save_data()

    async def async_handle_delete_item(call: ServiceCall):
        """Delete an item."""
        item_id = call.data[ATTR_ITEM_ID]
        if item_id in storage.data["items"]:
            del storage.data["items"][item_id]
            await storage.async_save_data()

    hass.services.async_register(
        DOMAIN, "add_item", async_handle_add_item, schema=ITEM_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, "update_item", async_handle_update_item,
        schema=ITEM_SCHEMA.extend({
            vol.Required(ATTR_ITEM_ID): cv.string
        })
    )
    
    hass.services.async_register(
        DOMAIN, "delete_item", async_handle_delete_item,
        schema=vol.Schema({
            vol.Required(ATTR_ITEM_ID): cv.string
        })
    )
    
    # Frontend panel
    hass.http.register_static_path(
        "/local/pantry-panel.js",
        hass.config.path("custom_components/pantry/frontend/dist/pantry-panel.js"),
        False
    )
    
    hass.components.frontend.async_register_built_in_panel(
        "custom",
        "pantry_panel",
        "Pantry",
        "mdi:food-drumstick",
        "pantry_panel",
        {"js_url": "/local/pantry-panel.js"}
    )
    
    return True