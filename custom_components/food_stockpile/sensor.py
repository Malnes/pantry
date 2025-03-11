from __future__ import annotations
import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):
    async_add_entities([FoodStockpileSensor(hass)], update_before_add=True)


class FoodStockpileSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant):
        self._hass = hass
        self._state = 0
        self._attributes = {}
        self._name = "Food Stockpile"

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        """Could be the number of items that need attention (e.g. expired or below min)."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Contains the full list of items."""
        return self._attributes

    async def async_update(self):
        """Update sensor data."""
        data = self._hass.data[DOMAIN]["items"]
        # Count items that are expired or below min quantity
        # Build an attributes list for easy display in Developer Tools
        for item in data:
            # Remove duplicates or sort expiration dates if you want
            item["expiration_dates"] = sorted(list(set(item["expiration_dates"])))

        # Items needing attention
        low_items = [i for i in data if i["current_quantity"] < i["min_quantity"]]
        expired_items = []
        from datetime import datetime, date
        today = date.today()
        for i in data:
            for exp in i["expiration_dates"]:
                try:
                    exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                    if exp_date < today:
                        expired_items.append(i["item"])
                        break
                except:
                    pass
        
        # Just store them as top-level attributes for reference
        self._attributes = {
            "items": data,
            "items_below_min": [i["item"] for i in low_items],
            "items_expired_or_near_expiry": expired_items
        }

        # Optionally set state to number of items needing attention
        self._state = len(set(low_items + expired_items))
