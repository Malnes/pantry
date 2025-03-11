from homeassistant import config_entries
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN  # create a const.py with `DOMAIN = "food_stockpile"`

class FoodStockpileFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Create the config entry right away, no user options needed
            return self.async_create_entry(title="Food Stockpile", data={})

        # If no user input yet, show an (optional) form. E.g., if you wanted user fields:
        # form_schema = vol.Schema({
        #     vol.Required("some_option"): cv.string
        # })
        # return self.async_show_form(step_id="user", data_schema=form_schema)

        # For a single-step, no-data flow, just show a single button:
        return self.async_show_form(step_id="user")
