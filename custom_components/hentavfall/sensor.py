import logging
from datetime import date, time

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
# Import the time tracker helper and the callback type
from homeassistant.helpers.event import async_track_time_change
from homeassistant.core import callback, HomeAssistant

from .const import DOMAIN, WASTE_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
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
        
        # This will hold the function to cancel the midnight listener when the sensor is removed
        self._midnight_listener = None

    def _get_icon(self, waste_type):
        """Return a suitable icon for the waste type."""
        return {
            "Hageavfall": "mdi:leaf",
            "Papir": "mdi:package-variant-closed",
            "Matavfall": "mdi:food-apple-outline",
            "Restavfall": "mdi:trash-can",
            "Plastemballasje": "mdi:recycle",
        }.get(waste_type, "mdi:trash-can-outline")

    # --- NEW METHOD ---
    # This is called when the sensor is added to Home Assistant.
    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        # We call the update handler at midnight to re-evaluate the state
        self._midnight_listener = async_track_time_change(
            self.hass, self._handle_midnight_update, hour=0, minute=0, second=0
        )

    # --- NEW METHOD ---
    # This is called when the sensor is removed from Home Assistant.
    async def async_will_remove_from_hass(self) -> None:
        """Handle entity which will be removed."""
        await super().async_will_remove_from_hass()
        # Clean up the listener
        if self._midnight_listener:
            self._midnight_listener()
            self._midnight_listener = None
    
    # --- NEW METHOD ---
    # This callback function is triggered by the listener at midnight.
    @callback
    def _handle_midnight_update(self, *args) -> None:
        """Request a state update at midnight to ensure date accuracy."""
        # This tells Home Assistant to re-run the state property calculation
        self.async_schedule_update_ha_state(force_refresh=False)

    @property
    def state(self) -> date | None:
        """Return the state of the sensor (the next pickup date)."""
        # The logic here remains the same, but it will now be correctly re-run at midnight
        today = date.today()
        if self.coordinator.data is None:
            return None
        
        all_dates = self.coordinator.data.get(self._waste_type, [])
        
        # Find the next date that is today or in the future
        next_pickup = next((d for d in all_dates if d >= today), None)
        
        return next_pickup

    @property
    def extra_state_attributes(self):
        """Return other attributes."""
        if self.coordinator.data is None:
            return {"all_pickups": []}
            
        all_dates = self.coordinator.data.get(self._waste_type, [])
        
        # Format dates as strings for attributes
        formatted_dates = [d.isoformat() for d in all_dates]

        return {
            "all_pickups": formatted_dates,
        }