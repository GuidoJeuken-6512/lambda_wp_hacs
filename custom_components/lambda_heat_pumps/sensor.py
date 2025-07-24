"""Platform for Lambda WP sensor integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.template import Template, TemplateError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DOMAIN,
    SENSOR_TYPES,
    HP_SENSOR_TEMPLATES,
    BOIL_SENSOR_TEMPLATES,
    HC_SENSOR_TEMPLATES,
    BUFF_SENSOR_TEMPLATES,
    SOL_SENSOR_TEMPLATES,
    CALCULATED_SENSOR_TEMPLATES,
)
from .coordinator import LambdaDataUpdateCoordinator
from .utils import build_device_info, generate_base_addresses, generate_sensor_names
from .const_mapping import HP_ERROR_STATE  # noqa: F401
from .const_mapping import HP_STATE  # noqa: F401
from .const_mapping import HP_RELAIS_STATE_2ND_HEATING_STAGE  # noqa: F401
from .const_mapping import HP_OPERATING_STATE  # noqa: F401
from .const_mapping import HP_REQUEST_TYPE  # noqa: F401
from .const_mapping import BOIL_CIRCULATION_PUMP_STATE  # noqa: F401
from .const_mapping import BOIL_OPERATING_STATE  # noqa: F401
from .const_mapping import HC_OPERATING_STATE  # noqa: F401
from .const_mapping import HC_OPERATING_MODE  # noqa: F401
from .const_mapping import BUFF_OPERATING_STATE  # noqa: F401
from .const_mapping import BUFF_REQUEST_TYPE  # noqa: F401
from .const_mapping import SOL_OPERATING_STATE  # noqa: F401
from .const_mapping import MAIN_CIRCULATION_PUMP_STATE  # noqa: F401
from .const_mapping import MAIN_AMBIENT_OPERATING_STATE  # noqa: F401
from .const_mapping import MAIN_E_MANAGER_OPERATING_STATE  # noqa: F401

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lambda Heat Pumps sensors."""
    _LOGGER.debug("Setting up Lambda sensors for entry %s", entry.entry_id)

    # Migration bestehender Entitäten - entferne doppelte Sensoren mit "_2" Suffix
    entity_registry = async_get_entity_registry(hass)
    registry_entries = entity_registry.entities.get_entries_for_config_entry_id(entry.entry_id)
    
    for registry_entry in registry_entries:
        if "_2" in registry_entry.entity_id:
            _LOGGER.info(
                "Removing duplicate entity with '_2' suffix: %s",
                registry_entry.entity_id
            )
            entity_registry.async_remove(registry_entry.entity_id)

    # Get coordinator from hass.data
    coordinator_data = hass.data[DOMAIN][entry.entry_id]
    if not coordinator_data or "coordinator" not in coordinator_data:
        _LOGGER.error("No coordinator found for entry %s", entry.entry_id)
        return

    coordinator = coordinator_data["coordinator"]
    _LOGGER.debug("Found coordinator: %s", coordinator)

    # Get device counts from config
    num_hps = entry.data.get("num_hps", 1)
    num_boil = entry.data.get("num_boil", 1)
    num_buff = entry.data.get("num_buff", 0)
    num_sol = entry.data.get("num_sol", 0)
    num_hc = entry.data.get("num_hc", 1)

    # In Version 1.2.0 wurde use_legacy_modbus_names entfernt - immer True
    use_legacy_modbus_names = True
    name_prefix = entry.data.get("name", "").lower().replace(" ", "")

    # Create sensors for each device type using a generic loop
    sensors = []

    TEMPLATES = [
        ("hp", num_hps, HP_SENSOR_TEMPLATES),
        ("boil", num_boil, BOIL_SENSOR_TEMPLATES),
        ("buff", num_buff, BUFF_SENSOR_TEMPLATES),
        ("sol", num_sol, SOL_SENSOR_TEMPLATES),
        ("hc", num_hc, HC_SENSOR_TEMPLATES),
    ]

    for prefix, count, template in TEMPLATES:
        for idx in range(1, count + 1):
            base_address = generate_base_addresses(prefix, count)[idx]
            # Always use lowercased name_prefix for all entity_id/unique_id generation
            name_prefix_lc = name_prefix.lower() if name_prefix else ""
            for sensor_id, sensor_info in template.items():
                address = base_address + sensor_info["relative_address"]
                if coordinator.is_register_disabled(address):
                    _LOGGER.debug(
                        "Skipping sensor %s (address %d) because register is "
                        "disabled",
                        f"{prefix}{idx}_{sensor_id}",
                        address,
                    )
                    continue
                device_class = sensor_info.get("device_class")
                if not device_class and sensor_info.get("unit") == "°C":
                    device_class = SensorDeviceClass.TEMPERATURE
                elif not device_class and sensor_info.get("unit") == "W":
                    device_class = SensorDeviceClass.POWER
                elif not device_class and sensor_info.get("unit") == "Wh":
                    device_class = SensorDeviceClass.ENERGY

                # Prüfe auf Override-Name
                override_name = None
                if (
                    use_legacy_modbus_names
                    and hasattr(coordinator, "sensor_overrides")
                ):
                    override_name = coordinator.sensor_overrides.get(
                        f"{prefix}{idx}_{sensor_id}"
                    )
                if override_name:
                    name = override_name
                    sensor_id_final = f"{prefix}{idx}_{sensor_id}"
                    # Data key (original format)
                    entity_id = (
                        f"sensor.{name_prefix_lc}_{override_name}"
                    )
                    unique_id = f"{name_prefix_lc}_{override_name}"
                else:
                    prefix_upper = prefix.upper()
                    device_prefix = f"{prefix}{idx}"

                    if (
                        prefix == "hc"
                        and sensor_info.get("device_type") == "Climate"
                    ):
                        name = sensor_info["name"].format(idx)
                    else:
                        name = f"{prefix_upper}{idx} {sensor_info['name']}"

                    # Verwende die zentrale Namensgenerierung
                    names = generate_sensor_names(
                        device_prefix,
                        sensor_info["name"],
                        sensor_id,
                        name_prefix,
                        use_legacy_modbus_names
                    )

                    sensor_id_final = f"{prefix}{idx}_{sensor_id}"
                    entity_id = names["entity_id"]
                    unique_id = names["unique_id"]

                device_type = (
                    prefix.upper() if prefix in [
                        "hp",
                        "boil",
                        "hc",
                        "buff",
                        "sol",
                    ]
                    else sensor_info.get("device_type", "main")
                )

                sensors.append(
                    LambdaSensor(
                        coordinator=coordinator,
                        entry=entry,
                        sensor_id=sensor_id_final,
                        name=name,
                        unit=sensor_info.get("unit", ""),
                        address=address,
                        scale=sensor_info.get("scale", 1.0),
                        state_class=sensor_info.get("state_class", ""),
                        device_class=device_class,
                        relative_address=sensor_info.get(
                            "relative_address", 0
                        ),
                        data_type=sensor_info.get("data_type", None),
                        device_type=device_type,
                        txt_mapping=sensor_info.get("txt_mapping", False),
                        precision=sensor_info.get("precision", None),
                        entity_id=entity_id,
                        unique_id=unique_id,
                    )
                )

    # General Sensors (SENSOR_TYPES)
    for sensor_id, sensor_info in SENSOR_TYPES.items():
        address = sensor_info["address"]
        if coordinator.is_register_disabled(address):
            _LOGGER.debug(
                "Skipping general sensor %s (address %d) because register is "
                "disabled",
                sensor_id,
                address,
            )
            continue
        device_class = sensor_info.get("device_class")
        if not device_class and sensor_info.get("unit") == "°C":
            device_class = SensorDeviceClass.TEMPERATURE
        elif not device_class and sensor_info.get("unit") == "W":
            device_class = SensorDeviceClass.POWER
        elif not device_class and sensor_info.get("unit") == "Wh":
            device_class = SensorDeviceClass.ENERGY

        # Name und Entity-ID für General Sensors
        if use_legacy_modbus_names and "override_name" in sensor_info:
            name = sensor_info["override_name"]
            sensor_id_final = sensor_info["override_name"]
            _LOGGER.info(
                f"Override name for sensor '{sensor_id}': '{name}' "
                f"wird als Name und sensor_id verwendet."
            )
        else:
            name = sensor_info["name"]
            sensor_id_final = sensor_id

        # Verwende die zentrale Namensgenerierung für General Sensors
        # Für General Sensors ist der sensor_id der device_prefix
        names = generate_sensor_names(
            sensor_id,  # device_prefix für General Sensors ist der sensor_id
            sensor_info["name"],
            sensor_id_final,  # sensor_id für die Namensgenerierung
            name_prefix,
            use_legacy_modbus_names
        )

        entity_id = names["entity_id"]
        unique_id = names["unique_id"]

        sensors.append(
            LambdaSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_id=sensor_id_final,
                name=name,
                unit=sensor_info.get("unit", ""),
                address=address,
                scale=sensor_info.get("scale", 1.0),
                state_class=sensor_info.get("state_class", ""),
                device_class=device_class,
                relative_address=sensor_info.get("address", 0),
                data_type=sensor_info.get("data_type", None),
                device_type=sensor_info.get("device_type", None),
                txt_mapping=sensor_info.get("txt_mapping", False),
                precision=sensor_info.get("precision", None),
                entity_id=entity_id,
                unique_id=unique_id,
            )
        )

    # --- Cycling Total Sensors (echte Entities, keine Templates) ---
    cycling_modes = [
        ("heating", "heating_cycling_total"),
        ("hot_water", "hot_water_cycling_total"),
        ("cooling", "cooling_cycling_total"),
        ("defrost", "defrost_cycling_total"),
    ]
    cycling_sensor_count = 0
    cycling_sensor_ids = []
    cycling_entities = {}  # Dictionary für schnellen Zugriff

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in cycling_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            # Entity-ID und unique_id generieren
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names
            )
            cycling_sensor_ids.append(names["entity_id"])

            cycling_sensor = LambdaCyclingSensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
            )

            sensors.append(cycling_sensor)
            cycling_entities[names["entity_id"]] = cycling_sensor
            cycling_sensor_count += 1

    # --- Yesterday Cycling Sensors (echte Entities für Daily-Berechnung) ---
    yesterday_modes = [
        ("heating", "heating_cycling_yesterday"),
        ("hot_water", "hot_water_cycling_yesterday"),
        ("cooling", "cooling_cycling_yesterday"),
        ("defrost", "defrost_cycling_yesterday"),
    ]
    yesterday_sensor_count = 0
    yesterday_sensor_ids = []

    for hp_idx in range(1, num_hps + 1):
        for mode, template_id in yesterday_modes:
            template = CALCULATED_SENSOR_TEMPLATES[template_id]
            # Entity-ID und unique_id generieren
            device_prefix = f"hp{hp_idx}"
            names = generate_sensor_names(
                device_prefix,
                template["name"],
                template_id,
                name_prefix,
                use_legacy_modbus_names
            )
            yesterday_sensor_ids.append(names["entity_id"])

            yesterday_sensor = LambdaYesterdaySensor(
                hass=hass,
                entry=entry,
                sensor_id=template_id,
                name=names["name"],
                entity_id=names["entity_id"],
                unique_id=names["unique_id"],
                unit=template["unit"],
                state_class=template["state_class"],
                device_class=template["device_class"],
                device_type=template["device_type"],
                hp_index=hp_idx,
                mode=mode,
            )

            sensors.append(yesterday_sensor)
            yesterday_sensor_count += 1

    # Speichere die Cycling-Entities für schnellen Zugriff
    if "lambda_heat_pumps" not in hass.data:
        hass.data["lambda_heat_pumps"] = {}
    if entry.entry_id not in hass.data["lambda_heat_pumps"]:
        hass.data["lambda_heat_pumps"][entry.entry_id] = {}
    hass.data["lambda_heat_pumps"][entry.entry_id]["cycling_entities"] = cycling_entities
    _LOGGER.info(
        "Cycling-Sensoren erzeugt: %d, Entity-IDs: %s",
        cycling_sensor_count,
        cycling_sensor_ids,
    )
    _LOGGER.info(
        "Yesterday-Sensoren erzeugt: %d, Entity-IDs: %s",
        yesterday_sensor_count,
        yesterday_sensor_ids,
    )

    _LOGGER.info(
        "Alle Sensoren (inkl. Cycling) erzeugt: %d",
        len(sensors),
    )
    async_add_entities(sensors)

    # Load template sensors from template_sensor.py
    from .template_sensor import async_setup_entry as setup_template_sensors
    try:
        await setup_template_sensors(hass, entry, async_add_entities)
    except Exception as e:
        _LOGGER.error("Error setting up template sensors: %s", e)


# --- Entity-Klasse für Cycling Total Sensoren ---
class LambdaCyclingSensor(RestoreEntity, SensorEntity):
    """Cycling total sensor (echte Entity, Wert wird von increment_cycling_counter gesetzt)."""

    def __init__(self, hass, entry, sensor_id, name, entity_id, unique_id, unit, state_class, device_class, device_type, hp_index):
        self.hass = hass
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self.entity_id = entity_id
        self._unique_id = unique_id
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._hp_index = hp_index
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit
        self._attr_name = name
        self._attr_unique_id = unique_id
        # Initialisiere cycling_value mit 0
        self._cycling_value = 0
        # Yesterday-Wert für Daily-Berechnung
        self._yesterday_value = 0
        # Signal-Unsubscribe-Funktion
        self._unsub_dispatcher = None

        if state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif state_class == "total":
            self._attr_state_class = SensorStateClass.TOTAL
        elif state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None
        self._attr_device_class = device_class

    def set_cycling_value(self, value):
        """Set the cycling value and update state."""
        self._cycling_value = int(value)  # Stelle sicher, dass es ein Integer ist
        # Stelle sicher, dass der State korrekt aktualisiert wird
        self.async_write_ha_state()
        _LOGGER.debug(f"Cycling sensor {self.entity_id} value set to {value}")

    def update_yesterday_value(self):
        """Update yesterday value with current total value (called at midnight)."""
        old_yesterday = self._yesterday_value
        self._yesterday_value = self._cycling_value
        _LOGGER.info(f"Yesterday value updated for {self.entity_id}: {old_yesterday} -> {self._yesterday_value}")

    async def async_added_to_hass(self):
        """Initialize the sensor when added to Home Assistant."""
        await super().async_added_to_hass()
        
        last_state = None
        try:
            # Versuch 1: Standard-RestoreEntity Methode
            if hasattr(super(), 'async_get_last_state'):
                last_state = await super().async_get_last_state()
            # Versuch 2: HA-Interne Methode (für ältere Versionen)
            elif hasattr(self, 'async_get_last_state'):
                last_state = await self.async_get_last_state()
            # Fallback: Manueller State-Abruf
            else:
                current_state = self.hass.states.get(self.entity_id)
                if current_state and current_state.state not in (None, "unknown", "unavailable"):
                    last_state = current_state
        except Exception as e:
            _LOGGER.warning(f"State restore failed for {self.entity_id}: {e}")
        
        await self.restore_state(last_state)

        # Registriere Signal-Handler für Yesterday-Update
        from .automations import SIGNAL_UPDATE_YESTERDAY  # noqa: F401
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass,
            SIGNAL_UPDATE_YESTERDAY,
            self._handle_yesterday_update
        )

        # Schreibe den State sofort ins UI
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Clean up when entity is removed."""
        if self._unsub_dispatcher:
            self._unsub_dispatcher()
            self._unsub_dispatcher = None
        await super().async_will_remove_from_hass()

    async def restore_state(self, last_state):
        """Restore state from database to prevent reset on reload."""
        if last_state is not None:
            try:
                # Lade den letzten Wert aus der Datenbank
                last_value = last_state.state
                if last_value not in (None, "unknown", "unavailable"):
                    self._cycling_value = int(float(last_value))
                    _LOGGER.info(f"Cycling sensor {self.entity_id} restored from database: {self._cycling_value}")
                else:
                    # Fallback auf 0 nur wenn wirklich kein Wert in der DB
                    self._cycling_value = 0
                    _LOGGER.info(f"Cycling sensor {self.entity_id} initialized with 0 (no previous state)")
            except (ValueError, TypeError) as e:
                _LOGGER.warning(f"Could not restore state for {self.entity_id}: {e}, using 0")
                self._cycling_value = 0
        else:
            # Kein vorheriger State vorhanden, initialisiere mit 0
            self._cycling_value = 0
            _LOGGER.info(f"Cycling sensor {self.entity_id} initialized with 0 (no previous state)")

        # Stelle sicher, dass der Wert ein Integer ist
        self._cycling_value = int(self._cycling_value)

    @callback
    def _handle_yesterday_update(self, entry_id: str):
        """Handle yesterday update signal."""
        if entry_id == self._entry.entry_id:
            self.update_yesterday_value()

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def state_class(self):
        return self._attr_state_class

    @property
    def device_class(self):
        return self._attr_device_class

    @property
    def device_info(self):
        return build_device_info(self._entry)

    @property
    def native_value(self):
        """Return the current cycling value."""
        # Wert aus Attribut, Standard 0
        value = getattr(self, '_cycling_value', 0)
        if value is None:
            value = 0
        return int(value)  # Stelle sicher, dass es ein Integer ist

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "yesterday_value": self._yesterday_value,
            "hp_index": self._hp_index,
            "sensor_type": "cycling_total"
        }


class LambdaYesterdaySensor(RestoreEntity, SensorEntity):
    """Yesterday cycling sensor (speichert Total-Werte für Daily-Berechnung)."""

    def __init__(self, hass, entry, sensor_id, name, entity_id, unique_id, unit, state_class, device_class, device_type, hp_index, mode):
        self.hass = hass
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self.entity_id = entity_id
        self._unique_id = unique_id
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._hp_index = hp_index
        self._mode = mode
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_native_unit_of_measurement = unit
        self._attr_name = name
        self._attr_unique_id = unique_id
        # Yesterday-Wert (wird von Total-Sensor übernommen)
        self._yesterday_value = 0
        # Signal-Unsubscribe-Funktion
        self._unsub_dispatcher = None

        if state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif state_class == "total":
            self._attr_state_class = SensorStateClass.TOTAL
        elif state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            self._attr_state_class = None
        self._attr_device_class = device_class

    def update_yesterday_value(self, total_value):
        """Update yesterday value with current total value (called at midnight)."""
        old_yesterday = self._yesterday_value
        self._yesterday_value = int(total_value)
        _LOGGER.info(f"Yesterday sensor {self.entity_id} updated: {old_yesterday} -> {self._yesterday_value}")
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Initialize the sensor when added to Home Assistant."""
        await super().async_added_to_hass()
        
        last_state = None
        try:
            # Versuch 1: Standard-RestoreEntity Methode
            if hasattr(super(), 'async_get_last_state'):
                last_state = await super().async_get_last_state()
            # Versuch 2: HA-Interne Methode (für ältere Versionen)
            elif hasattr(self, 'async_get_last_state'):
                last_state = await self.async_get_last_state()
            # Fallback: Manueller State-Abruf
            else:
                current_state = self.hass.states.get(self.entity_id)
                if current_state and current_state.state not in (None, "unknown", "unavailable"):
                    last_state = current_state
        except Exception as e:
            _LOGGER.warning(f"State restore failed for {self.entity_id}: {e}")
        
        await self.restore_state(last_state)

        # Registriere Signal-Handler für Yesterday-Update
        from .automations import SIGNAL_UPDATE_YESTERDAY  # noqa: F401
        self._unsub_dispatcher = async_dispatcher_connect(
            self.hass,
            SIGNAL_UPDATE_YESTERDAY,
            self._handle_yesterday_update
        )

        # Schreibe den State sofort ins UI
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        """Clean up when entity is removed."""
        if self._unsub_dispatcher:
            self._unsub_dispatcher()
            self._unsub_dispatcher = None
        await super().async_will_remove_from_hass()

    async def restore_state(self, last_state):
        """Restore state from database to prevent reset on reload."""
        if last_state is not None:
            try:
                # Lade den letzten Wert aus der Datenbank
                last_value = last_state.state
                if last_value not in (None, "unknown", "unavailable"):
                    self._yesterday_value = int(float(last_value))
                    _LOGGER.info(f"Yesterday sensor {self.entity_id} restored from database: {self._yesterday_value}")
                else:
                    # Fallback auf 0 nur wenn wirklich kein Wert in der DB
                    self._yesterday_value = 0
                    _LOGGER.info(f"Yesterday sensor {self.entity_id} initialized with 0 (no previous state)")
            except (ValueError, TypeError) as e:
                _LOGGER.warning(f"Could not restore state for {self.entity_id}: {e}, using 0")
                self._yesterday_value = 0
        else:
            # Kein vorheriger State vorhanden, initialisiere mit 0
            self._yesterday_value = 0
            _LOGGER.info(f"Yesterday sensor {self.entity_id} initialized with 0 (no previous state)")

        # Stelle sicher, dass der Wert ein Integer ist
        self._yesterday_value = int(self._yesterday_value)

    @callback
    def _handle_yesterday_update(self, entry_id: str):
        """Handle yesterday update signal."""
        if entry_id == self._entry.entry_id:
            # Hole den aktuellen Total-Wert vom entsprechenden Total-Sensor
            total_sensor_id = f"{self._mode}_cycling_total"
            device_prefix = f"hp{self._hp_index}"
            names = generate_sensor_names(
                device_prefix,
                CALCULATED_SENSOR_TEMPLATES[total_sensor_id]["name"],
                total_sensor_id,
                self._entry.data.get("name", "").lower().replace(" ", ""),
                self._entry.data.get("use_legacy_modbus_names", False)
            )
            total_entity_id = names["entity_id"]

            # Hole den aktuellen Wert vom Total-Sensor
            total_state = self.hass.states.get(total_entity_id)
            if total_state and total_state.state not in (None, "unknown", "unavailable"):
                try:
                    total_value = int(float(total_state.state))
                    self.update_yesterday_value(total_value)
                except (ValueError, TypeError):
                    _LOGGER.warning(f"Could not parse total value from {total_entity_id}: {total_state.state}")

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def native_unit_of_measurement(self):
        return self._unit

    @property
    def state_class(self):
        return self._attr_state_class

    @property
    def device_class(self):
        return self._attr_device_class

    @property
    def device_info(self):
        """Return device info."""
        return build_device_info(self._entry)

    @property
    def native_value(self):
        """Return the yesterday value."""
        value = getattr(self, '_yesterday_value', 0)
        if value is None:
            value = 0
        return int(value)

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        return {
            "mode": self._mode,
            "hp_index": self._hp_index,
            "sensor_type": "cycling_yesterday"
        }


class LambdaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Lambda sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: LambdaDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        name: str,
        unit: str,
        address: int,
        scale: float,
        state_class: str,
        device_class: SensorDeviceClass,
        relative_address: int,
        data_type: str,
        device_type: str,
        txt_mapping: bool = False,
        precision: int | float | None = None,
        entity_id: str | None = None,
        unique_id: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_id = sensor_id
        self._attr_name = name
        self._attr_unique_id = unique_id  # Immer die generierte ID verwenden
        self.entity_id = entity_id or f"sensor.{sensor_id}"
        self._unit = unit
        self._address = address
        self._scale = scale
        self._state_class = state_class
        self._device_class = device_class
        self._relative_address = relative_address
        self._data_type = data_type
        self._device_type = device_type
        self._txt_mapping = txt_mapping
        self._precision = precision

        _LOGGER.debug(
            "Sensor initialized with ID: %s and config: %s",
            sensor_id,
            {
                "name": name,
                "unit": unit,
                "address": address,
                "scale": scale,
                "state_class": state_class,
                "device_class": device_class,
                "relative_address": relative_address,
                "data_type": data_type,
                "device_type": device_type,
                "txt_mapping": txt_mapping,
                "precision": precision,
            },
        )

        self._is_state_sensor = txt_mapping

        if self._is_state_sensor:
            self._attr_device_class = None
            self._attr_state_class = None
            self._attr_native_unit_of_measurement = None
            self._attr_suggested_display_precision = None
        else:
            self._attr_native_unit_of_measurement = unit
            if precision is not None:
                self._attr_suggested_display_precision = precision
            if unit == "°C":
                self._attr_device_class = SensorDeviceClass.TEMPERATURE
            elif unit == "W":
                self._attr_device_class = SensorDeviceClass.POWER
            elif unit == "Wh":
                self._attr_device_class = SensorDeviceClass.ENERGY
            if state_class:
                if state_class == "total":
                    self._attr_state_class = SensorStateClass.TOTAL
                elif state_class == "total_increasing":
                    self._attr_state_class = SensorStateClass.TOTAL_INCREASING
                elif state_class == "measurement":
                    self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        # In Version 1.2.0 wurde use_legacy_modbus_names entfernt - immer True
        use_legacy_modbus_names = True
        if (
            use_legacy_modbus_names
            and hasattr(self.coordinator, "sensor_overrides")
        ):
            override_name = self.coordinator.sensor_overrides.get(
                self._sensor_id
            )
            if override_name:
                # Verwende den Override-Namen als sensor_id
                _LOGGER.debug(
                    "Overriding sensor_id from %s to %s",
                    self._sensor_id,
                    override_name,
                )
                self._sensor_id = override_name
                return override_name
        return self._attr_name

    @property
    def native_value(self) -> float | str | None:
        if not self.coordinator.data:
            return None
        value = self.coordinator.data.get(self._sensor_id)
        if value is None:
            return None
        if self._is_state_sensor:
            try:
                numeric_value = int(float(value))
            except (ValueError, TypeError):
                return f"Unknown state ({value})"

            # Extract base name without index
            # (e.g. "HP1 Operating State" -> "Operating State")
            base_name = self._attr_name
            if self._device_type and self._device_type.upper() in base_name:
                # Remove prefix and index (e.g. "HP1 " or "BOIL2 ")
                base_name = ' '.join(base_name.split()[1:])
            # Ersetze auch Bindestriche durch Unterstriche
            mapping_name = (
                f"{self._device_type.upper()}_"
                f"{base_name.upper().replace(' ', '_').replace('-', '_')}"
            )
            try:
                state_mapping = globals().get(mapping_name)
                if state_mapping is not None:
                    return state_mapping.get(
                        numeric_value,
                        f"Unknown state ({numeric_value})"
                    )
                _LOGGER.warning(
                    "No state mapping found f. sensor '%s' (tried mapping: %s)"
                    "with value %s. Sensor details: device_type=%s, "
                    "register=%d, data_type=%s. This sensor is marked as state"
                    "sensor (txt_mapping=True) but no corresponding mapping "
                    "dictionary was found.",
                    self._attr_name,
                    mapping_name,
                    numeric_value,
                    self._device_type,
                    self._relative_address,
                    self._data_type,
                )
                return f"Unknown mapping for state ({numeric_value})"
            except Exception as e:
                _LOGGER.error(
                    "Error accessing mapping dictionary: %s",
                    str(e),
                )
                return f"Error loading mappings ({numeric_value})"
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def device_info(self):
        """Return device info for this sensor."""
        return build_device_info(self._entry)


class LambdaTemplateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Lambda template sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: LambdaDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_id: str,
        name: str,
        unit: str,
        state_class: str,
        device_class: SensorDeviceClass,
        device_type: str,
        precision: int | float | None = None,
        entity_id: str | None = None,
        unique_id: str | None = None,
        template_str: str = "",
    ) -> None:
        """Initialize the template sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._sensor_id = sensor_id
        self._name = name
        self._unit = unit
        self._state_class = state_class
        self._device_class = device_class
        self._device_type = device_type
        self._precision = precision
        self._entity_id = entity_id
        self._unique_id = unique_id
        self._template_str = template_str
        self._state = None
        _LOGGER.info(
            f"Template-Sensor erstellt: {self._name} (ID: {self._sensor_id}) mit Template: {self._template_str}"
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self._unique_id

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor."""
        return self._state

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor."""
        return self._unit

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class of the sensor."""
        if self._state_class == "measurement":
            return SensorStateClass.MEASUREMENT
        elif self._state_class == "total":
            return SensorStateClass.TOTAL
        elif self._state_class == "total_increasing":
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class of the sensor."""
        if self._device_class == "temperature":
            return SensorDeviceClass.TEMPERATURE
        elif self._device_class == "power":
            return SensorDeviceClass.POWER
        elif self._device_class == "energy":
            return SensorDeviceClass.ENERGY
        return None

    @property
    def device_info(self):
        """Return device info."""
        return build_device_info(self._entry)

    @callback
    def handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        try:
            template = Template(self._template_str, self.hass)
            rendered_value = template.async_render()
            if rendered_value is None or rendered_value == "unavailable":
                self._state = None
                return
            if isinstance(rendered_value, str) and (
                rendered_value.startswith("{{")
                or "states(" in rendered_value
            ):
                _LOGGER.debug(
                    "Template not yet ready for sensor %s, waiting for dependencies",
                    self._sensor_id
                )
                self._state = None
                return
            try:
                float_value = float(rendered_value)
                if self._precision is not None:
                    self._state = round(float_value, self._precision)
                else:
                    self._state = float_value
                _LOGGER.info(
                    f"Template-Sensor berechnet: {self._name} (ID: {self._sensor_id}) = {self._state}"
                )
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Could not convert template result to float for sensor %s: %s",
                    self._sensor_id, rendered_value
                )
                self._state = None
        except TemplateError as err:
            _LOGGER.warning(
                "Template error for sensor %s: %s", self._sensor_id, err
            )
            self._state = None
        except Exception as err:
            _LOGGER.warning(
                "Error rendering template for sensor %s: %s",
                self._sensor_id, err
            )
            self._state = None
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.handle_coordinator_update()
