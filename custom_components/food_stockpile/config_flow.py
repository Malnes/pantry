from homeassistant import config_entries
from .const import DOMAIN  # Or just set DOMAIN = "food_stockpile" here

class FoodStockpileFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Create a config entry with no user settings
            return self.async_create_entry(title="Food Stockpile", data={})

        # Present a simple form (or skip directly to create_entry)
        return self.async_show_form(step_id="user")
