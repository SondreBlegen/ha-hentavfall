import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_GUID

class HentavfallConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HentAvfall."""

    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Here you could add validation to check if the GUID is valid
            # by making a quick test API call, but for simplicity, we'll skip that.
            
            # Ensure no other entry with the same GUID exists
            await self.async_set_unique_id(user_input[CONF_GUID])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Hentavfall Schedule", data=user_input
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_GUID): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )