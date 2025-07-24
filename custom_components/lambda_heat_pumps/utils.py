"""Utility functions for Lambda Heat Pumps integration."""
from __future__ import annotations

import logging
import os
import yaml
import aiofiles

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import (
    async_get as async_get_entity_registry
)
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity_component import async_update_entity

from .const import (
    BASE_ADDRESSES,
    CALCULATED_SENSOR_TEMPLATES,
)

_LOGGER = logging.getLogger(__name__)


def get_compatible_sensors(sensor_templates: dict, fw_version: int) -> dict:
    """Return only sensors compatible with the given firmware version.
    Args:
       sensor_templates: Dictionary of sensor templates
       fw_version: The firmware version to check against
    Returns:
       Filtered dictionary of compatible sensors
    """
    return {
        k: v
        for k, v in sensor_templates.items()
        if v.get("firmware_version", 1) <= fw_version
    }


def build_device_info(entry):
    """
    Build device_info dict for Home Assistant device registry.
    """
    DOMAIN = entry.domain if hasattr(entry, "domain") else "lambda_heat_pumps"
    entry_id = entry.entry_id
    fw_version = entry.data.get("firmware_version", "unknown")
    host = entry.data.get("host")
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": entry.data.get("name", "Lambda WP"),
        "manufacturer": "Lambda",
        "model": fw_version,
        "configuration_url": f"http://{host}",
        "sw_version": fw_version,
        "entry_type": None,
        "suggested_area": None,
        "via_device": None,
        "hw_version": None,
        "serial_number": None,
    }


async def migrate_lambda_config(hass: HomeAssistant) -> bool:
    """Migrate existing lambda_wp_config.yaml to include cycling_offsets.

    Returns:
        bool: True if migration was performed, False otherwise
    """
    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    if not os.path.exists(lambda_config_path):
        _LOGGER.debug("No existing lambda_wp_config.yaml found, no migration needed")
        return False

    try:
        # Read current config
        async with aiofiles.open(lambda_config_path, "r") as file:
            content = await file.read()
            current_config = yaml.safe_load(content)

        if not current_config:
            _LOGGER.debug("Empty config file, no migration needed")
            return False

        # Check if cycling_offsets already exists
        if "cycling_offsets" in current_config:
            _LOGGER.info(
                "lambda_wp_config.yaml already contains cycling_offsets - "
                "no migration needed"
            )
            return False

        _LOGGER.info("Migrating lambda_wp_config.yaml to include cycling_offsets")

        # Create backup
        backup_path = lambda_config_path + ".backup"
        async with aiofiles.open(backup_path, "w") as backup_file:
            await backup_file.write(content)
        _LOGGER.info("Created backup at %s", backup_path)

        # Add cycling_offsets section
        current_config["cycling_offsets"] = {
            "hp1": {
                "heating_cycling_total": 0,
                "hot_water_cycling_total": 0,
                "cooling_cycling_total": 0,
                "defrost_cycling_total": 0
            }
        }

        # Add documentation comment
        if "# Cycling counter offsets" not in content:
            # Insert cycling_offsets documentation before the existing sections
            cycling_docs = """# Cycling counter offsets for total sensors
# These offsets are added to the calculated cycling counts
# Useful when replacing heat pumps or resetting counters
# Example:
#cycling_offsets:
#  hp1:
#    heating_cycling_total: 0      # Offset for HP1 heating total cycles
#    hot_water_cycling_total: 0    # Offset for HP1 hot water total cycles
#    cooling_cycling_total: 0      # Offset for HP1 cooling total cycles
#  hp2:
#    heating_cycling_total: 1500   # Example: HP2 already had 1500 heating cycles
#    hot_water_cycling_total: 800  # Example: HP2 already had 800 hot water cycles
#    cooling_cycling_total: 200    # Example: HP2 already had 200 cooling cycles

"""
            # Find a good place to insert the documentation
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('disabled_registers:'):
                    insert_pos = i
                    break

            lines.insert(insert_pos, cycling_docs.rstrip())
            content = '\n'.join(lines)

        # Write updated config
        async with aiofiles.open(lambda_config_path, "w") as file:
            await file.write(content)

        _LOGGER.info(
            "Successfully migrated lambda_wp_config.yaml to version 1.1.0 - "
            "Added cycling_offsets section with default values for hp1. "
            "Backup created at %s.backup", lambda_config_path
        )
        return True

    except Exception as e:
        _LOGGER.error("Error during config migration: %s", e)
        return False


async def load_lambda_config(hass: HomeAssistant) -> dict:
    """Load complete Lambda configuration from lambda_wp_config.yaml."""
    # First, try to migrate if needed
    await migrate_lambda_config(hass)

    config_dir = hass.config.config_dir
    lambda_config_path = os.path.join(config_dir, "lambda_wp_config.yaml")

    default_config = {
        "disabled_registers": set(),
        "sensors_names_override": {},
        "cycling_offsets": {}
    }

    if not os.path.exists(lambda_config_path):
        _LOGGER.warning(
            "lambda_wp_config.yaml not found, using default configuration"
        )
        return default_config

    try:
        async with aiofiles.open(lambda_config_path, "r") as file:
            content = await file.read()
            config = yaml.safe_load(content)

            if not config:
                _LOGGER.warning(
                    "lambda_wp_config.yaml is empty, using default configuration"
                )
                return default_config

            # Load disabled registers
            disabled_registers = set()
            if "disabled_registers" in config:
                try:
                    disabled_registers = set(int(x) for x in config["disabled_registers"])
                except (ValueError, TypeError) as e:
                    _LOGGER.error(
                        "Invalid disabled_registers format: %s", e
                    )
                    disabled_registers = set()

            # Load sensor overrides
            sensors_names_override = {}
            if "sensors_names_override" in config:
                try:
                    for override in config["sensors_names_override"]:
                        if "id" in override and "override_name" in override:
                            sensors_names_override[override["id"]] = (
                                override["override_name"]
                            )
                except (TypeError, KeyError) as e:
                    _LOGGER.error(
                        "Invalid sensors_names_override format: %s", e
                    )
                    sensors_names_override = {}

            # Load cycling offsets
            cycling_offsets = {}
            if "cycling_offsets" in config:
                try:
                    cycling_offsets = config["cycling_offsets"]
                    # Validate cycling offsets structure
                    for device, offsets in cycling_offsets.items():
                        if not isinstance(offsets, dict):
                            _LOGGER.warning(
                                "Invalid cycling_offsets format for device %s",
                                device
                            )
                            continue
                        for offset_type, value in offsets.items():
                            if not isinstance(value, (int, float)):
                                _LOGGER.warning(
                                    "Invalid cycling offset value for %s.%s: %s",
                                    device, offset_type, value
                                )
                                cycling_offsets[device][offset_type] = 0
                except (TypeError, KeyError) as e:
                    _LOGGER.error(
                        "Invalid cycling_offsets format: %s", e
                    )
                    cycling_offsets = {}

            _LOGGER.debug(
                "Loaded Lambda config: %d disabled registers, %d sensor "
                "overrides, %d device offsets",
                len(disabled_registers),
                len(sensors_names_override),
                len(cycling_offsets)
            )

            return {
                "disabled_registers": disabled_registers,
                "sensors_names_override": sensors_names_override,
                "cycling_offsets": cycling_offsets
            }

    except Exception as e:
        _LOGGER.error(
            "Error loading configuration from lambda_wp_config.yaml: %s",
            str(e),
        )
        return default_config


# Keep the old function for backward compatibility
async def load_disabled_registers(hass: HomeAssistant) -> set[int]:
    """Load disabled registers from lambda_wp_config in config directory.

    DEPRECATED: Use load_lambda_config() instead.
    """
    config = await load_lambda_config(hass)
    return config["disabled_registers"]


def is_register_disabled(address: int, disabled_registers: set[int]) -> bool:
    """Check if a register is disabled.

    Args:
        address: The register address to check
        disabled_registers: Set of disabled register addresses

    Returns:
        bool: True if the register is disabled, False otherwise
    """
    is_disabled = address in disabled_registers
    if is_disabled:
        _LOGGER.debug(
            "Register %d is disabled (in set: %s)",
            address,
            disabled_registers,
        )
    return is_disabled


def generate_base_addresses(device_type: str, count: int) -> dict:
    """Generate base addresses for a given device type and count.

    Args:
        device_type: Type of device (hp, boil, buff, sol, hc)
        count: Number of devices

    Returns:
        dict: Dictionary with device numbers as keys
        and base addresses as values
    """
    base_addresses = BASE_ADDRESSES

    start_address = base_addresses.get(device_type, 0)
    if start_address == 0:
        return {}

    return {i: start_address + (i - 1) * 100 for i in range(1, count + 1)}


def to_signed_16bit(val):
    """Wandelt einen 16-Bit-Wert in signed um."""
    return val - 0x10000 if val >= 0x8000 else val


def to_signed_32bit(val):
    """Wandelt einen 32-Bit-Wert in signed um."""
    return val - 0x100000000 if val >= 0x80000000 else val


def clamp_to_int16(value: float, context: str = "value") -> int:
    """Clamp a value to int16 range (-32768 to 32767).

    Args:
        value: The value to clamp
        context: Context string for logging (e.g., "temperature", "power")

    Returns:
        int: The clamped value in int16 range
    """
    raw_value = int(value)
    if raw_value < -32768:
        _LOGGER.warning(
            "%s value %d is below int16 minimum (-32768), clamping to -32768",
            context.capitalize(), raw_value
        )
        return -32768
    elif raw_value > 32767:
        _LOGGER.warning(
            "%s value %d is above int16 maximum (32767), clamping to 32767",
            context.capitalize(), raw_value
        )
        return 32767
    else:
        return raw_value


def generate_sensor_names(
    device_prefix: str,
    sensor_name: str,
    sensor_id: str,
    name_prefix: str,
    use_legacy_modbus_names: bool
) -> dict:
    """Generate consistent sensor names, entity IDs, and unique IDs.

    Args:
        device_prefix: Device prefix like "hp1", "boil1", etc. or sensor_id for general sensors
        sensor_name: Human readable sensor name like "COP Calculated"
        sensor_id: Sensor identifier like "cop_calc"
        name_prefix: Name prefix like "eu08l" (used in legacy mode)
        use_legacy_modbus_names: Whether to use legacy naming convention

    Returns:
        dict: Contains 'name', 'entity_id', and 'unique_id'
    """
    # Display name logic - identical to sensor.py
    # Both legacy and standard modes use the same display name format
    # The name_prefix will be added automatically by Home Assistant's device naming
    if device_prefix == sensor_id:
        # Für General Sensors nur den sensor_name verwenden
        display_name = sensor_name
    else:
        display_name = f"{device_prefix.upper()} {sensor_name}"

    # Always use lowercase for name_prefix to unify entity_id generation
    name_prefix_lc = name_prefix.lower() if name_prefix else ""

    # Entity ID und unique_id wie in der alten Version generieren
    if use_legacy_modbus_names:
        # Für General Sensors nur name_prefix_sensor_id verwenden
        if device_prefix == sensor_id:
            entity_id = f"sensor.{name_prefix_lc}_{sensor_id}"
            unique_id = f"{name_prefix_lc}_{sensor_id}"
        else:
            entity_id = (
                f"sensor.{name_prefix_lc}_{device_prefix}_{sensor_id}"
            )
            unique_id = f"{name_prefix_lc}_{device_prefix}_{sensor_id}"
    else:
        # Für General Sensors (device_prefix == sensor_id) nur sensor_id verwenden
        if device_prefix == sensor_id:
            entity_id = f"sensor.{sensor_id}"
            unique_id = f"{sensor_id}"
        else:
            entity_id = f"sensor.{device_prefix}_{sensor_id}"
            unique_id = f"{device_prefix}_{sensor_id}"

    return {
        "name": display_name,
        "entity_id": entity_id,
        "unique_id": unique_id
    }


def generate_template_entity_prefix(
    device_prefix: str,
    name_prefix: str,
    use_legacy_modbus_names: bool
) -> str:
    """Generate entity prefix for templates based on naming mode.

    Args:
        device_prefix: Device prefix like "hp1", "boil1", etc.
        name_prefix: Name prefix like "eu08l" (used in legacy mode)
        use_legacy_modbus_names: Whether to use legacy naming convention

    Returns:
        str: Entity prefix for use in templates
    """
    if use_legacy_modbus_names:
        return f"{name_prefix}_{device_prefix}"
    else:
        return device_prefix


# --- Cycling Counter Increment Function ---

async def increment_cycling_counter(
    hass: HomeAssistant,
    mode: str,
    hp_index: int,
    name_prefix: str,
    use_legacy_modbus_names: bool = False,
    cycling_offsets: dict = None,
):
    """
    Increment the cycling_total counter for a given mode and heat pump index.
    This should be called only on a real flank (state change)!

    Args:
        hass: HomeAssistant instance
        mode: One of ["heating", "hot_water", "cooling", "defrost"]
        hp_index: Index of the heat pump (1-based)
        name_prefix: Name prefix (e.g. "eu08l")
        use_legacy_modbus_names: Use legacy entity naming
        cycling_offsets: Optional dict with cycling offsets from config
    """

    sensor_id = f"{mode}_cycling_total"
    device_prefix = f"hp{hp_index}"
    names = generate_sensor_names(device_prefix, CALCULATED_SENSOR_TEMPLATES[sensor_id]["name"], sensor_id, name_prefix, use_legacy_modbus_names)
    entity_id = names["entity_id"]

    # Check if entity is already registered
    entity_registry = async_get_entity_registry(hass)
    entity_entry = entity_registry.async_get(entity_id)
    if entity_entry is None:
        _LOGGER.warning(f"Skipping cycling counter increment: {entity_id} not yet registered")
        return

    # Zusätzliche Prüfung: Ist die Entity tatsächlich verfügbar?
    state_obj = hass.states.get(entity_id)
    if state_obj is None:
        _LOGGER.warning(f"Skipping cycling counter increment: {entity_id} state not available yet")
        return

    # Get current state
    if state_obj.state in (None, STATE_UNKNOWN, "unknown"):
        current = 0
    else:
        try:
            current = int(float(state_obj.state))
        except Exception:
            current = 0

    # Offset aus cycling_offsets laden
    offset = 0
    if cycling_offsets is not None:
        device_key = device_prefix
        if device_key in cycling_offsets:
            offset = int(cycling_offsets[device_key].get(sensor_id, 0))

    new_value = int(current + 1)

    # Versuche die Entity-Instanz zu finden
    cycling_entity = None
    try:
        # Suche in der neuen Cycling-Entities-Struktur
        for entry_id, comp_data in hass.data.get("lambda_heat_pumps", {}).items():
            if isinstance(comp_data, dict) and "cycling_entities" in comp_data:
                cycling_entity = comp_data["cycling_entities"].get(entity_id)
                if cycling_entity:
                    break
    except Exception as e:
        _LOGGER.debug(f"Error searching for entity {entity_id}: {e}")

    final_value = int(new_value + offset)
    if cycling_entity is not None and hasattr(cycling_entity, "set_cycling_value"):
        cycling_entity.set_cycling_value(final_value)
        _LOGGER.info(f"Cycling counter incremented: {entity_id} = {final_value} (was {current}, offset {offset}) [entity updated]")
    else:
        # Fallback: State setzen wie bisher
        _LOGGER.warning(f"Cycling entity {entity_id} not found, using fallback state update")
        hass.states.async_set(entity_id, final_value, state_obj.attributes if state_obj else {})
        _LOGGER.info(f"Cycling counter incremented: {entity_id} = {final_value} (was {current}, offset {offset}) [state only]")

    # Optional: Entity zum Update zwingen (z.B. für Recorder)
    try:
        await async_update_entity(hass, entity_id)
    except Exception as e:
        _LOGGER.debug(f"Could not force update for {entity_id}: {e}")


# --- Entity Migration Functions ---

async def migrate_to_legacy_names(hass: HomeAssistant, entry) -> bool:
    """Migrate entities to use legacy naming convention (with name_prefix).
    
    This function migrates all Lambda entities to use the legacy naming convention
    where unique_id always includes the name_prefix (e.g., eu08l_ambient_temperature).
    
    Args:
        hass: HomeAssistant instance
        entry: ConfigEntry for the Lambda integration
        
    Returns:
        bool: True if migration was performed, False if no migration needed
    """
    entity_registry = async_get_entity_registry(hass)
    name_prefix = entry.data.get("name", "eu08l").lower().replace(" ", "")
    migrated_count = 0
    removed_count = 0
    
    _LOGGER.info(f"Starting entity migration to legacy naming for {name_prefix}")
    
    # Get all Lambda entities
    lambda_entities = [
        entity for entity in entity_registry.entities.values()
        if entity.config_entry_id == entry.entry_id
    ]
    
    # Track which entities we've migrated to avoid duplicates
    migrated_unique_ids = set()
    
    for entity in lambda_entities:
        current_unique_id = entity.unique_id
        
        # Skip if already using legacy naming
        if current_unique_id.startswith(f"{name_prefix}_"):
            continue
            
        # Generate new unique_id with legacy naming
        if "_" in current_unique_id:
            # Extract sensor_id from current unique_id
            parts = current_unique_id.split("_", 1)
            if len(parts) == 2:
                sensor_id = parts[1]
                new_unique_id = f"{name_prefix}_{sensor_id}"
            else:
                # Fallback: just prepend name_prefix
                new_unique_id = f"{name_prefix}_{current_unique_id}"
        else:
            # Simple case: just prepend name_prefix
            new_unique_id = f"{name_prefix}_{current_unique_id}"
        
        # Check if new unique_id already exists (conflict)
        if new_unique_id in migrated_unique_ids:
            # Remove the conflicting entity instead of migrating
            try:
                entity_registry.async_remove(entity.entity_id)
                removed_count += 1
                _LOGGER.info(f"Removed conflicting entity {entity.entity_id} (duplicate unique_id: {new_unique_id})")
            except Exception as e:
                _LOGGER.error(f"Failed to remove conflicting entity {entity.entity_id}: {e}")
            continue
        
        # Update entity in registry
        try:
            entity_registry.async_update_entity(
                entity.entity_id,
                new_unique_id=new_unique_id
            )
            migrated_unique_ids.add(new_unique_id)
            migrated_count += 1
            _LOGGER.info(f"Migrated {entity.entity_id}: {current_unique_id} → {new_unique_id}")
        except Exception as e:
            _LOGGER.error(f"Failed to migrate {entity.entity_id}: {e}")
    
    if migrated_count > 0 or removed_count > 0:
        _LOGGER.info(f"✅ Entity migration completed: {migrated_count} entities migrated, {removed_count} conflicts removed")
        return True
    else:
        _LOGGER.info("ℹ️ No entities needed migration")
        return False


async def cleanup_duplicate_entities(hass: HomeAssistant, entry) -> bool:
    """Clean up duplicate entities that were created during migration.
    
    This function removes entities that have conflicting unique_ids after migration.
    
    Args:
        hass: HomeAssistant instance
        entry: ConfigEntry for the Lambda integration
        
    Returns:
        bool: True if cleanup was performed, False if no cleanup needed
    """
    entity_registry = async_get_entity_registry(hass)
    name_prefix = entry.data.get("name", "eu08l").lower().replace(" ", "")
    removed_count = 0
    
    _LOGGER.info(f"Starting cleanup of duplicate entities for {name_prefix}")
    
    # Get all Lambda entities
    lambda_entities = [
        entity for entity in entity_registry.entities.values()
        if entity.config_entry_id == entry.entry_id
    ]
    
    # Find entities with duplicate unique_ids
    unique_id_count = {}
    for entity in lambda_entities:
        unique_id = entity.unique_id
        if unique_id not in unique_id_count:
            unique_id_count[unique_id] = []
        unique_id_count[unique_id].append(entity)
    
    # Remove duplicates (keep the first one, remove the rest)
    for unique_id, entities in unique_id_count.items():
        if len(entities) > 1:
            # Sort by entity_id to ensure consistent removal
            entities.sort(key=lambda e: e.entity_id)
            # Keep the first entity, remove the rest
            for entity in entities[1:]:
                try:
                    entity_registry.async_remove(entity.entity_id)
                    removed_count += 1
                    _LOGGER.info(f"Removed duplicate entity {entity.entity_id} (unique_id: {unique_id})")
                except Exception as e:
                    _LOGGER.error(f"Failed to remove duplicate entity {entity.entity_id}: {e}")
    
    if removed_count > 0:
        _LOGGER.info(f"✅ Duplicate cleanup completed: {removed_count} duplicate entities removed")
        return True
    else:
        _LOGGER.info("ℹ️ No duplicate entities found")
        return False
