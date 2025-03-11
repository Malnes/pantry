from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

class PantrySensor(SensorEntity):
    def __init__(self, data):
        self._data = data
        self._state = "OK"

    @property
    def name(self):
        return "Pantry"

    @property
    def unique_id(self):
        return "pantry_sensor_1"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {"items": self._data.get("items", [])}

    def update_data(self, data):
        self._data = data
        self.async_write_ha_state()
