import logging
from datetime import date, datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WASTE_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        HentavfallSensor(coordinator, waste_type)
        for waste_type in WASTE_TYPES.values()
    ]
    async_add_entities(sensors, True)


class HentavfallSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Hentavfall sensor."""

    def __init__(self, coordinator, waste_type):
        super().__init__(coordinator)
        self._waste_type = waste_type
        self._attr_name = f"Next {waste_type} Pickup"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{waste_type}"
        self._attr_icon = self._get_icon(waste_type)
        self._attr_device_class = "date"

    def _get_icon(self, waste_type):
        """Return a suitable icon for the waste type."""
        return {
            "Hageavfall": "mdi:leaf",
            "Papir": "mdi:package-variant-closed",
            "Matavfall": "mdi:food-apple-outline",
            "Restavfall": "mdi:trash-can",
            "Plastemballasje": "mdi:recycle",
        }.get(waste_type, "mdi:trash-can-outline")

    @property
    def state(self):
        """Return the state of the sensor (the next pickup date)."""
        today = date.today()
        all_dates = self.coordinator.data.get(self._waste_type, [])
        
        # Find the next date that is today or in the future
        next_pickup = next((d for d in all_dates if d >= today), None)
        
        return next_pickup

    @property
    def extra_state_attributes(self):
        """Return other attributes."""
        all_dates = self.coordinator.data.get(self._waste_type, [])
        
        # Format dates as strings for attributes
        formatted_dates = [d.isoformat() for d in all_dates]

        return {
            "all_pickups": formatted_dates,
        }