"""Modbus utilities for Lambda Heat Pumps integration."""
import logging
import importlib.metadata as pkgMetadata
from packaging import version
from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)

_PYMODBUS_VERSION = version.parse(pkgMetadata.version('pymodbus'))
_PYMODBUS_3_0 = version.parse('3.0')
_PYMODBUS_2_0 = version.parse('2.0')


def read_holding_registers(client: ModbusTcpClient, address, count, slave_id=1):
    """Read holding registers with compatibility."""
    try:
        if _PYMODBUS_VERSION >= _PYMODBUS_3_0:
            return client.read_holding_registers(address, count=count, slave=slave_id)
        elif _PYMODBUS_VERSION >= _PYMODBUS_2_0:
            return client.read_holding_registers(address, count, slave_id)
        else:
            _LOGGER.error("Your pymodbus version is too old: %s", _PYMODBUS_VERSION)
            return None
    except Exception as e:
        _LOGGER.error("Error reading holding registers: %s", e)
        return None


def write_register(client: ModbusTcpClient, address, value, slave_id=1):
    """Write single register with compatibility."""
    try:
        if _PYMODBUS_VERSION >= _PYMODBUS_3_0:
            return client.write_register(address, value, slave=slave_id)
        elif _PYMODBUS_VERSION >= _PYMODBUS_2_0:
            return client.write_register(address, value, slave_id)
        else:
            _LOGGER.error("Your pymodbus version is too old: %s", _PYMODBUS_VERSION)
            return None
    except Exception as e:
        _LOGGER.error("Error writing register: %s", e)
        return None


def write_registers(client: ModbusTcpClient, address, values, slave_id=1):
    """Write multiple registers with compatibility."""
    try:
        if _PYMODBUS_VERSION >= _PYMODBUS_3_0:
            return client.write_registers(address, values, slave=slave_id)
        elif _PYMODBUS_VERSION >= _PYMODBUS_2_0:
            return client.write_registers(address, values, slave_id)
        else:
            _LOGGER.error("Your pymodbus version is too old: %s", _PYMODBUS_VERSION)
            return None
    except Exception as e:
        _LOGGER.error("Error writing registers: %s", e)
        return None


def read_input_registers(client: ModbusTcpClient, address, count, slave_id=1):
    """Read input registers with compatibility."""
    try:
        if _PYMODBUS_VERSION >= _PYMODBUS_3_0:
            return client.read_input_registers(address, count=count, slave=slave_id)
        elif _PYMODBUS_VERSION >= _PYMODBUS_2_0:
            return client.read_input_registers(address, count, slave_id)
        else:
            _LOGGER.error("Your pymodbus version is too old: %s", _PYMODBUS_VERSION)
            return None
    except Exception as e:
        _LOGGER.error("Error reading input registers: %s", e)
        return None
