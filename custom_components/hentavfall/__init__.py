import async_timeout
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HentavfallApi
from .const import DOMAIN, CONF_GUID

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up HentAvfall from a config entry."""
    guid = entry.data[CONF_GUID]
    session = async_get_clientsession(hass)
    api = HentavfallApi(guid, session)

    async def async_update_data():
        """Fetch data from API."""
        try:
            async with async_timeout.timeout(10):
                data = await api.fetch_data()
                if not data:
                    raise UpdateFailed("No data received from API")
                return data
        except asyncio.TimeoutError as exc:
            raise UpdateFailed("Timeout communicating with API") from exc
        except Exception as exc:
            raise UpdateFailed(f"Error communicating with API: {exc}") from exc

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Hentavfall Sensor",
        update_method=async_update_data,
        update_interval=timedelta(hours=12),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok