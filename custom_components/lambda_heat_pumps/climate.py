"""Climate platform for Lambda integration (template-basiert)."""
from __future__ import annotations
import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, 
    CLIMATE_TEMPLATES,
    DEFAULT_HOT_WATER_MIN_TEMP,
    DEFAULT_HOT_WATER_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
)
from .utils import generate_base_addresses, build_device_info, generate_sensor_names
from .modbus_utils import write_registers

_LOGGER = logging.getLogger(__name__)


class LambdaClimateEntity(CoordinatorEntity, ClimateEntity):
    """Template-basierte Lambda Climate Entity."""

    _attr_should_poll = False
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def __init__(self, coordinator, entry, climate_type, idx, base_address):
        super().__init__(coordinator)
        self._entry = entry
        self._climate_type = climate_type  # "hot_water" oder "heating_circuit"
        self._idx = idx
        self._base_address = base_address
        self._template = CLIMATE_TEMPLATES[climate_type]

        # Hole den Legacy-Modbus-Namen-Switch aus der Config
        # In Version 1.2.0 wurde use_legacy_modbus_names entfernt - immer True
        use_legacy_modbus_names = True
        name_prefix = entry.data.get("name", "").lower().replace(" ", "")

        # Verwende die Werte aus der CLIMATE_TEMPLATES Konfiguration
        device_type = self._template["device_type"]  # "boil" oder "hc"
        sensor_id = climate_type  # "hot_water" oder "heating_circuit"

        # Verwende die zentrale Namensgenerierung
        device_prefix = f"{device_type}{idx}"
        names = generate_sensor_names(
            device_prefix,
            self._template["name"],
            sensor_id,
            name_prefix,
            use_legacy_modbus_names
        )

        # Setze die Namen und IDs
        self._attr_name = names["name"]
        self._attr_unique_id = names["unique_id"]
        self.entity_id = names["entity_id"]

        # Temperaturbereich aus Entry-Optionen lesen
        if climate_type == "hot_water":
            self._attr_min_temp = entry.options.get(
                "hot_water_min_temp", DEFAULT_HOT_WATER_MIN_TEMP
            )
            self._attr_max_temp = entry.options.get(
                "hot_water_max_temp", DEFAULT_HOT_WATER_MAX_TEMP
            )
        else:  # heating_circuit
            self._attr_min_temp = entry.options.get(
                "heating_circuit_min_temp", DEFAULT_HEATING_CIRCUIT_MIN_TEMP
            )
            self._attr_max_temp = entry.options.get(
                "heating_circuit_max_temp", DEFAULT_HEATING_CIRCUIT_MAX_TEMP
            )

        self._attr_target_temperature_step = self._template.get(
            "precision", 0.5
        )
        self._attr_temperature_unit = self._template.get("unit", "°C")
        
        # HVAC-Modi aus CLIMATE_TEMPLATES lesen
        hvac_modes_set = self._template.get("hvac_mode", {"heat"})
        self._attr_hvac_modes = [HVACMode(mode) for mode in hvac_modes_set]
        self._attr_hvac_mode = HVACMode.HEAT  # Default-Modus

    @property
    def current_temperature(self):
        key = (
            f"boil{self._idx}_actual_high_temperature"
            if self._climate_type == "hot_water"
            else f"hc{self._idx}_room_device_temperature"
        )
        return self.coordinator.data.get(key)

    @property
    def target_temperature(self):
        key = (
            f"boil{self._idx}_target_high_temperature"
            if self._climate_type == "hot_water"
            else f"hc{self._idx}_target_room_temperature"
        )
        return self.coordinator.data.get(key)

    @property
    def state_class(self):
        return self._template.get("state_class")

    @property
    def device_info(self):
        return build_device_info(self._entry)

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get("temperature")
        if temperature is None:
            return
        reg_addr = self._base_address + self._template["relative_set_address"]
        scale = self._template["scale"]
        raw_value = int(temperature / scale)
        _LOGGER.info(
            "[Climate] Write target temperature: entity=%s, address=%s, "
            "value(raw)=%s, value(temp)=%s",
            self.entity_id,
            reg_addr,
            raw_value,
            temperature
        )
        result = await self.hass.async_add_executor_job(
            write_registers,
            self.coordinator.client,
            reg_addr,
            [raw_value],
            self._entry.data.get("slave_id", 1),
        )
        if hasattr(result, "isError") and result.isError():
            _LOGGER.error("Failed to write target temperature: %s", result)
            return
        key = (
            f"boil{self._idx}_target_high_temperature"
            if self._climate_type == "hot_water"
            else f"hc{self._idx}_target_room_temperature"
        )
        self.coordinator.data[key] = temperature
        await self.coordinator.async_refresh()
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Lambda Heat Pumps climate entities (template-basiert)."""
    _LOGGER.debug(
        "Setting up Lambda climate entities for entry %s", entry.entry_id
    )
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    num_boil = entry.data.get("num_boil", 1)
    num_hc = entry.data.get("num_hc", 1)
    entities = []

    # Boiler
    boil_addresses = generate_base_addresses("boil", num_boil)
    for idx in range(1, num_boil + 1):
        entities.append(
            LambdaClimateEntity(
                coordinator,
                entry,
                "hot_water",  # climate_type aus CLIMATE_TEMPLATES
                idx,
                boil_addresses[idx]
            )
        )

    # Heating Circuits
    hc_addresses = generate_base_addresses("hc", num_hc)
    for idx in range(1, num_hc + 1):
        entity_key = f"room_temperature_entity_{idx}"
        if not entry.options.get(entity_key):
            _LOGGER.debug(
                "No room temperature entity configured for heating circuit %s "
                "in entry %s, skipping entity creation.",
                idx,
                entry.entry_id
            )
            continue
        entities.append(
            LambdaClimateEntity(
                coordinator,
                entry,
                "heating_circuit",  # climate_type aus CLIMATE_TEMPLATES
                idx,
                hc_addresses[idx]
            )
        )

    async_add_entities(entities)
