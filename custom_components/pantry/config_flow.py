from homeassistant import config_entries

class PantryConfigFlow(config_entries.ConfigFlow, domain="pantry"):
    async def async_step_user(self, user_input=None):
        return self.async_create_entry(title="Pantry", data={})