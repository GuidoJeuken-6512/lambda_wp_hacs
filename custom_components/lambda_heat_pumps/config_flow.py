"""Config flow for Lambda WP integration."""

from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_HOST,
    DEFAULT_FIRMWARE,
    DEFAULT_ROOM_THERMOSTAT_CONTROL,
    DEFAULT_PV_SURPLUS,
    DEFAULT_NUM_HPS,
    DEFAULT_NUM_BOIL,
    DEFAULT_NUM_HC,
    DEFAULT_NUM_BUFFER,
    DEFAULT_NUM_SOLAR,
    DEFAULT_HOT_WATER_MIN_TEMP,
    DEFAULT_HOT_WATER_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
    DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
    DEFAULT_UPDATE_INTERVAL,
    CONF_SLAVE_ID,
    FIRMWARE_VERSION,
    CONF_ROOM_TEMPERATURE_ENTITY,
    CONF_PV_POWER_SENSOR_ENTITY,
    MAX_NUM_HPS,
    MAX_NUM_BOIL,
    MAX_NUM_HC,
    MAX_NUM_BUFFER,
    MAX_NUM_SOLAR,
)
from .modbus_utils import read_holding_registers

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect."""
    from pymodbus.client import ModbusTcpClient

    client = ModbusTcpClient(data[CONF_HOST], port=data[CONF_PORT])
    try:
        if not client.connect():
            raise CannotConnect("Could not connect to Modbus TCP")

        # Test read of a register to verify connection
        result = await hass.async_add_executor_job(
            read_holding_registers,
            client,
            0,  # Start address
            1,  # Number of registers to read
            data[CONF_SLAVE_ID],
        )

        if result.isError():
            raise CannotConnect("Failed to read from device")

    except Exception as ex:
        _LOGGER.error("Connection test failed: %s", ex)
        raise CannotConnect("Failed to connect to device") from ex
    finally:
        client.close()


class LambdaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Lambda WP."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is None:
            user_input = {}

        # Default-Werte aus bestehendem Eintrag holen, falls vorhanden
        current_entries = self._async_current_entries()
        existing_data = current_entries[0].data if current_entries else {}
        existing_options = (
            dict(current_entries[0].options) if current_entries else {}
        )

        # Die Übersetzungen werden automatisch
        # von Home Assistant übernommen

        # Pflichtfelder prüfen
        required_fields = [CONF_NAME, CONF_HOST, CONF_PORT, CONF_SLAVE_ID]
        if not all(k in user_input and user_input[k] for k in required_fields):
            # Formular anzeigen, wenn Eingaben fehlen
            firmware_options = list(FIRMWARE_VERSION.keys())
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_NAME,
                            default=user_input.get(
                                CONF_NAME,
                                existing_data.get(CONF_NAME, DEFAULT_NAME),
                            ),
                        ): selector.TextSelector(),
                        vol.Required(
                            CONF_HOST,
                            default=user_input.get(
                                CONF_HOST,
                                existing_data.get(CONF_HOST, DEFAULT_HOST),
                            ),
                        ): selector.TextSelector(),
                        vol.Required(
                            CONF_PORT,
                            default=int(
                                user_input.get(
                                    CONF_PORT,
                                    existing_data.get(CONF_PORT, DEFAULT_PORT),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=65535,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            CONF_SLAVE_ID,
                            default=int(
                                user_input.get(
                                    CONF_SLAVE_ID,
                                    existing_data.get(
                                        CONF_SLAVE_ID, DEFAULT_SLAVE_ID
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=255,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_hps",
                            default=int(
                                user_input.get(
                                    "num_hps",
                                    existing_data.get(
                                        "num_hps", DEFAULT_NUM_HPS
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                max=MAX_NUM_HPS,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_boil",
                            default=int(
                                user_input.get(
                                    "num_boil",
                                    existing_data.get(
                                        "num_boil", DEFAULT_NUM_BOIL
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=MAX_NUM_BOIL,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_hc",
                            default=int(
                                user_input.get(
                                    "num_hc",
                                    existing_data.get(
                                        "num_hc", DEFAULT_NUM_HC
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=MAX_NUM_HC,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_buff",
                            default=int(
                                user_input.get(
                                    "num_buff",
                                    existing_data.get(
                                        "num_buff", DEFAULT_NUM_BUFFER
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=MAX_NUM_BUFFER,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Required(
                            "num_sol",
                            default=int(
                                user_input.get(
                                    "num_sol",
                                    existing_data.get(
                                        "num_sol", DEFAULT_NUM_SOLAR
                                    ),
                                )
                            ),
                        ): selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=MAX_NUM_SOLAR,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            )
                        ),
                        vol.Optional(
                            "firmware_version",
                            default=user_input.get(
                                "firmware_version",
                                existing_data.get(
                                    "firmware_version", DEFAULT_FIRMWARE
                                ),
                            ),
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=firmware_options,
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                        # use_legacy_modbus_names removed in version 1.2.0 - always True
                    }
                ),
                errors=errors,
            )

        try:
            # Convert numeric values to integers
            for key in [
                "port",
                "slave_id",
                "num_hps",
                "num_boil",
                "num_hc",
                "num_buff",
                "num_sol",
            ]:
                if key in user_input:
                    user_input[key] = int(user_input[key])

            # Ergänze fehlende Pflichtfelder aus existing_data oder Default
            if CONF_NAME not in user_input or not user_input[CONF_NAME]:
                user_input[CONF_NAME] = existing_data.get(
                    CONF_NAME, DEFAULT_NAME
                )
            await validate_input(self.hass, user_input)
            if CONF_NAME not in user_input or not user_input[CONF_NAME]:
                errors["base"] = "name_required"
            else:
                # Erstelle den Eintrag mit Standard-Optionen
                default_options = {
                    # Immer false beim initialen Setup
                    "room_thermostat_control": False,
                    "pv_surplus": DEFAULT_PV_SURPLUS,
                    "hot_water_min_temp": user_input.get(
                        "hot_water_min_temp",
                        existing_options.get(
                            "hot_water_min_temp", DEFAULT_HOT_WATER_MIN_TEMP
                        ),
                    ),
                    "hot_water_max_temp": user_input.get(
                        "hot_water_max_temp",
                        existing_options.get(
                            "hot_water_max_temp", DEFAULT_HOT_WATER_MAX_TEMP
                        ),
                    ),
                    "heating_circuit_min_temp": user_input.get(
                        "heating_circuit_min_temp",
                        existing_options.get(
                            "heating_circuit_min_temp",
                            DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
                        ),
                    ),
                    "heating_circuit_max_temp": user_input.get(
                        "heating_circuit_max_temp",
                        existing_options.get(
                            "heating_circuit_max_temp",
                            DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
                        ),
                    ),
                    "heating_circuit_temp_step": user_input.get(
                        "heating_circuit_temp_step",
                        existing_options.get(
                            "heating_circuit_temp_step",
                            DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
                        ),
                    ),
                    "firmware_version": user_input.get(
                        "firmware_version",
                        existing_options.get(
                            "firmware_version", DEFAULT_FIRMWARE
                        ),
                    ),
                }
                _LOGGER.debug(
                    "ConfigFlow: Erstelle neuen Eintrag mit data=%s, "
                    "options=%s",
                    user_input,
                    default_options,
                )
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                    options=default_options,
                )
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        # Zeige das vollständige Formular mit allen Feldern an
        firmware_options = list(FIRMWARE_VERSION.keys())
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=user_input.get(
                            CONF_NAME,
                            existing_data.get(CONF_NAME, DEFAULT_NAME),
                        ),
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_HOST,
                        default=user_input.get(
                            CONF_HOST,
                            existing_data.get(CONF_HOST, DEFAULT_HOST),
                        ),
                    ): selector.TextSelector(),
                    vol.Required(
                        CONF_PORT,
                        default=int(
                            user_input.get(
                                CONF_PORT,
                                existing_data.get(CONF_PORT, DEFAULT_PORT),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=65535,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_SLAVE_ID,
                        default=int(
                            user_input.get(
                                CONF_SLAVE_ID,
                                existing_data.get(
                                    CONF_SLAVE_ID, DEFAULT_SLAVE_ID
                                ),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=255,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        "num_hps",
                        default=int(
                            user_input.get(
                                "num_hps",
                                existing_data.get("num_hps", DEFAULT_NUM_HPS),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=MAX_NUM_HPS,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        "num_boil",
                        default=int(
                            user_input.get(
                                "num_boil",
                                existing_data.get(
                                    "num_boil", DEFAULT_NUM_BOIL
                                ),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=MAX_NUM_BOIL,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        "num_hc",
                        default=int(
                            user_input.get(
                                "num_hc",
                                existing_data.get("num_hc", DEFAULT_NUM_HC),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=MAX_NUM_HC,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        "num_buff",
                        default=int(
                            user_input.get(
                                "num_buff",
                                existing_data.get(
                                    "num_buff", DEFAULT_NUM_BUFFER
                                ),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=MAX_NUM_BUFFER,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        "num_sol",
                        default=int(
                            user_input.get(
                                "num_sol",
                                existing_data.get(
                                    "num_sol", DEFAULT_NUM_SOLAR
                                ),
                            )
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=MAX_NUM_SOLAR,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        "firmware_version",
                        default=user_input.get(
                            "firmware_version",
                            existing_data.get(
                                "firmware_version", DEFAULT_FIRMWARE
                            ),
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=firmware_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    # use_legacy_modbus_names removed in version 1.2.0 - always True
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        # config_entry argument is unused, kept for interface compatibility
        return LambdaOptionsFlow(config_entry)


class LambdaOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        # Stelle sicher, dass options ein Dictionary ist
        # und alle erforderlichen Schlüssel enthält
        self._options = {
            "room_thermostat_control": DEFAULT_ROOM_THERMOSTAT_CONTROL,
            "pv_surplus": DEFAULT_PV_SURPLUS,
            "hot_water_min_temp": DEFAULT_HOT_WATER_MIN_TEMP,
            "hot_water_max_temp": DEFAULT_HOT_WATER_MAX_TEMP,
            "heating_circuit_min_temp": DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
            "heating_circuit_max_temp": DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
            "heating_circuit_temp_step": DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
            "firmware_version": DEFAULT_FIRMWARE,
        }
        if config_entry.options:
            self._options.update(dict(config_entry.options))

    def _cleanup_disabled_options(self):
        """Clean up sensor configurations when options are disabled."""
        # Clean up room thermostat configurations if disabled
        if not self._options.get("room_thermostat_control", False):
            num_hc = self._config_entry.data.get("num_hc", 1)
            for hc_idx in range(1, num_hc + 1):
                entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(hc_idx)
                if entity_key in self._options:
                    del self._options[entity_key]

        # Clean up PV sensor configuration if disabled
        if not self._options.get("pv_surplus", False):
            if CONF_PV_POWER_SENSOR_ENTITY in self._options:
                del self._options[CONF_PV_POWER_SENSOR_ENTITY]

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step of the options flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validierung der Temperaturwerte
            min_temp = user_input.get(
                "hot_water_min_temp", DEFAULT_HOT_WATER_MIN_TEMP
            )
            max_temp = user_input.get(
                "hot_water_max_temp", DEFAULT_HOT_WATER_MAX_TEMP
            )
            if min_temp >= max_temp:
                errors["hot_water_min_temp"] = "min_temp_higher"

            hc_min_temp = user_input.get(
                "heating_circuit_min_temp",
                DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
            )
            hc_max_temp = user_input.get(
                "heating_circuit_max_temp",
                DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
            )
            if hc_min_temp >= hc_max_temp:
                errors["heating_circuit_min_temp"] = "min_temp_higher"

            if not errors:
                # Store the updated options
                self._options.update(user_input)
                self._cleanup_disabled_options()

                # Entscheiden, welcher Schritt als nächstes kommt
                if self._options.get("room_thermostat_control"):
                    return await self.async_step_thermostat_sensor()
                if self._options.get("pv_surplus"):
                    return await self.async_step_pv_sensor()

                return self.async_create_entry(
                    title="", data=self._options
                )

        return await self._show_init_form(errors)

    async def _show_init_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show the initial options form."""
        options_schema = {
            vol.Optional(
                "hot_water_min_temp",
                default=self._options.get(
                    "hot_water_min_temp", DEFAULT_HOT_WATER_MIN_TEMP
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=30,
                    max=70,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "hot_water_max_temp",
                default=self._options.get(
                    "hot_water_max_temp", DEFAULT_HOT_WATER_MAX_TEMP
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=30,
                    max=70,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "heating_circuit_min_temp",
                default=self._options.get(
                    "heating_circuit_min_temp",
                    DEFAULT_HEATING_CIRCUIT_MIN_TEMP,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=10,
                    max=40,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "heating_circuit_max_temp",
                default=self._options.get(
                    "heating_circuit_max_temp",
                    DEFAULT_HEATING_CIRCUIT_MAX_TEMP,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=10,
                    max=40,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "heating_circuit_temp_step",
                default=self._options.get(
                    "heating_circuit_temp_step",
                    DEFAULT_HEATING_CIRCUIT_TEMP_STEP,
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1,
                    max=2.0,
                    step=0.1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "firmware_version",
                default=self._options.get(
                    "firmware_version",
                    DEFAULT_FIRMWARE
                ),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(FIRMWARE_VERSION.keys()),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                "room_thermostat_control",
                default=self._options.get(
                    "room_thermostat_control",
                    DEFAULT_ROOM_THERMOSTAT_CONTROL
                ),
            ): (
                selector.BooleanSelector()
            ),
            vol.Optional(
                "pv_surplus",
                default=self._options.get("pv_surplus", DEFAULT_PV_SURPLUS),
            ): selector.BooleanSelector(),
            vol.Optional(
                "update_interval",
                default=self._options.get(
                    "update_interval", DEFAULT_UPDATE_INTERVAL
                ),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=300,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(options_schema),
            errors=errors or {},
        )

    async def async_step_thermostat_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the thermostat sensor selection step."""
        if user_input is not None:
            self._options.update(user_input)
            # Decide if we need to show the PV sensor step
            if self._options.get("pv_surplus"):
                return await self.async_step_pv_sensor()
            return self.async_create_entry(title="", data=self._options)

        # Dynamically build schema for thermostat sensors
        num_hc = self._config_entry.data.get("num_hc", 0)
        temperature_sensors = await self._get_entities("temperature")
        schema = {}

        for i in range(1, num_hc + 1):
            entity_key = CONF_ROOM_TEMPERATURE_ENTITY.format(i)
            schema[
                vol.Optional(
                    entity_key,
                    description={
                        "suggested_value": self._options.get(entity_key)
                    },
                )
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    include_entities=temperature_sensors
                )
            )

        return self.async_show_form(
            step_id="thermostat_sensor", data_schema=vol.Schema(schema)
        )

    async def async_step_pv_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the PV sensor selection step."""
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        # Logik zur Abfrage der Entitäten
        power_sensors = await self._get_entities("power")

        schema = {
            vol.Optional(
                "pv_power_sensor_entity",
                description={
                    "suggested_value": self._options.get(
                        "pv_power_sensor_entity"
                    )
                },
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    include_entities=power_sensors
                )
            )
        }

        return self.async_show_form(
            step_id="pv_sensor", data_schema=vol.Schema(schema)
        )

    async def _get_entities(self, device_class: str) -> list[str]:
        """Get a list of external entities with a specific device class."""
        from homeassistant.helpers.entity_registry import async_get

        registry = async_get(self.hass)
        own_entity_ids = {
            entity.entity_id
            for entity in registry.entities.values()
            if entity.config_entry_id == self._config_entry.entry_id
        }

        entities = []
        for entity in self.hass.states.async_all():
            if entity.entity_id in own_entity_ids:
                continue

            if entity.domain != "sensor":
                continue

            attributes = entity.attributes
            is_match = False
            if device_class == "temperature":
                if attributes.get("device_class") == "temperature":
                    is_match = True
            elif device_class == "power":
                if attributes.get("device_class") == "power" or attributes.get(
                    "unit_of_measurement"
                ) in ("W", "kW"):
                    is_match = True

            if is_match:
                entities.append(entity.entity_id)

        # Sort by friendly name
        entities.sort(key=lambda eid: self.hass.states.get(eid).name.lower())

        return entities

    async def _test_connection(self, user_input: dict[str, Any]) -> None:
        """Test the connection to the Modbus device."""
        # user_input argument is unused, kept for interface compatibility
        pass


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
