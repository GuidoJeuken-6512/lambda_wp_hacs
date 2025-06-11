"""The Lambda Heat Pumps integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import asyncio
from typing import Dict, Any
import os
import aiofiles

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import ConfigEntryNotReady
import voluptuous as vol

from .const import DOMAIN, DEBUG_PREFIX
from .coordinator import LambdaDataUpdateCoordinator
from .services import async_setup_services, async_unload_services
from .utils import generate_base_addresses

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)
VERSION = "1.0.0"

# Diese Konstante teilt Home Assistant mit, dass die Integration Übersetzungen hat
TRANSLATION_SOURCES = {DOMAIN: "translations"}

# Lock für das Reloading
_reload_lock = asyncio.Lock()

PLATFORMS = [
    Platform.SENSOR,
    Platform.CLIMATE,
]

# Konfigurationsschema für die Integration
CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional("debug", default=False): bool,
    })
})

LAMBDA_WP_CONFIG_TEMPLATE = """# Lambda WP configuration
# This file is used by Lambda WP Integration to define the configuration of Lambda WP.
# The file is created during the installation of the Lambda WP Integration and can then be edited with the file editor or visual studio code.
# Modbus registrations that are not required can be deactivated here.
# Disabled registrations as an example:
#disabled_registers:
# - 2004 # boil1_actual_circulation_temp

# overwritten sensor names as an example:
# these override the names of the sensors created by the Lambda WP integration.
#sensors_names_override:
#- id: actual_heating_capacity
#  override_name: Hp_QP_heating
# sensors_names_override does only functions if use_legacy_modbus_names is set to true!!!


disabled_registers:
 - 100000 # this sensor does not exits, this is just an example

sensors_names_override:
- id: name_of_the_sensor_to_override_example
  override_name: new_name_of_the_sensor_example
"""

def setup_debug_logging(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up debug logging for the integration."""
    # hass argument is unused, kept for interface compatibility
    if config.get("debug", False):
        logging.getLogger(DEBUG_PREFIX).setLevel(logging.DEBUG)
        _LOGGER.info("Debug logging enabled for %s", DEBUG_PREFIX)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Lambda integration."""
    setup_debug_logging(hass, config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lambda Heat Pumps from a config entry."""
    _LOGGER.debug("Setting up Lambda integration with config: %s", entry.data)
    
    # Prüfe, ob lambda_wp_config.yaml existiert, sonst anlegen
    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")
    if not os.path.exists(lambda_config_path):
        async with aiofiles.open(lambda_config_path, "w") as f:
            await f.write(LAMBDA_WP_CONFIG_TEMPLATE)
    
    # Generate base addresses based on configured device counts
    num_hps = entry.data.get("num_hps", 1)
    num_boil = entry.data.get("num_boil", 1)
    num_buff = entry.data.get("num_buff", 0)
    num_sol = entry.data.get("num_sol", 0)
    num_hc = entry.data.get("num_hc", 1)
    
    _LOGGER.debug("Device counts - HPs: %d, Boilers: %d, Buffers: %d, Solar: %d, HCs: %d",
                 num_hps, num_boil, num_buff, num_sol, num_hc)
    
    # Log generated base addresses direkt ohne Variablen
    _LOGGER.debug(
        "Generated base addresses - HP: %s, Boil: %s, Buff: %s, Sol: %s, HC: %s",
        generate_base_addresses('hp', num_hps),
        generate_base_addresses('boil', num_boil),
        generate_base_addresses('buff', num_buff),
        generate_base_addresses('sol', num_sol),
        generate_base_addresses('hc', num_hc)
    )
    
    # Create coordinator
    coordinator = LambdaDataUpdateCoordinator(hass, entry)
    
    try:
        await coordinator.async_init()
        # Warte auf die erste Datenabfrage
        await coordinator.async_refresh()
        
        if not coordinator.data:
            _LOGGER.error("Failed to fetch initial data from Lambda device")
            return False

        # Store coordinator
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}
        _LOGGER.debug("Stored coordinator in hass.data[%s][%s]", DOMAIN, entry.entry_id)

        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Beim ersten Setup die Services registrieren
        if len(hass.data[DOMAIN]) == 1:
            await async_setup_services(hass)

        # Registriere Update-Listener
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

        return True
    except Exception as ex:
        _LOGGER.error("Failed to setup Lambda integration: %s", ex)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Reloading Lambda integration after config change for entry %s", entry.entry_id)
    
    # Use a lock to prevent multiple simultaneous reloads
    async with _reload_lock:
        try:
            # First, try to unload the entire integration
            try:
                await async_unload_entry(hass, entry)
            except Exception as ex:
                _LOGGER.error("Error during initial unload: %s", ex)
                # Continue anyway, as we want to force a reload

            # Wait a moment to ensure everything is unloaded
            await asyncio.sleep(1)

            # Now try to set up the entry again
            try:
                # Create a new coordinator
                coordinator = LambdaDataUpdateCoordinator(hass, entry)
                await coordinator.async_init()
                await coordinator.async_refresh()

                if not coordinator.data:
                    _LOGGER.error("Failed to fetch initial data after reload")
                    return

                # Store the coordinator
                hass.data.setdefault(DOMAIN, {})
                hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

                # Set up platforms
                await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

                # Set up services if this is the first entry
                if len(hass.data[DOMAIN]) == 1:
                    await async_setup_services(hass)

                # Register update listener
                entry.async_on_unload(entry.add_update_listener(async_reload_entry))

                _LOGGER.debug("Successfully reloaded Lambda integration for entry %s", entry.entry_id)
            except Exception as ex:
                _LOGGER.error("Error setting up entry after reload: %s", ex)
                # Clean up if setup failed
                if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
                    hass.data[DOMAIN].pop(entry.entry_id, None)
        except Exception as ex:
            _LOGGER.error("Unexpected error during reload: %s", ex)
