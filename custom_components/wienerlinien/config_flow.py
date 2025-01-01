"""Config flow for Wienerlinien integration."""
from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN, CONF_STOPS, CONF_FIRST_NEXT

class WienerlinienConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(f"wienerlinien_{user_input[CONF_STOPS]}")
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"Stop {user_input[CONF_STOPS]}", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_STOPS): str,
                vol.Optional(CONF_FIRST_NEXT, default="first"): vol.In(["first", "next"]),
            }),
            errors=errors,
        )
