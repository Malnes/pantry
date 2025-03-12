import logging
from homeassistant.helpers.storage import Store
from .const import DOMAIN, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)

class PantryStorage:
    def __init__(self, hass):
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = {}

    async def async_load_data(self):
        if not self.data:
            data = await self.store.async_load()
            self.data = data if data else {"items": {}}
        return self.data

    async def async_save_data(self):
        await self.store.async_save(self.data)