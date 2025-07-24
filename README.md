# Lambda Heat Pumps Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40GuidoJeuken--6512-blue.svg)](https://github.com/GuidoJeuken-6512)
[![version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Deutsche Version siehe unten / German version see below**

---

# 🇺🇸 English

## 🚀 Quickstart

**Lambda Heat Pumps** is a Home Assistant custom integration for Lambda heat pumps via Modbus/TCP.

### HACS Installation
1. Install HACS (if not already done)
2. Add this repo as a custom repository: `GuidoJeuken-6512/lambda_wp_hacs` (category: Integration)
3. Search for "Lambda Heat Pumps" in HACS, install, and restart Home Assistant

## ✨ Features

- **Full Modbus/TCP integration** for Lambda heat pumps
- **Dynamic sensor/entity detection** based on firmware
- **Configurable number of devices** (heat pumps, boilers, heating circuits, buffer tanks, solar modules)
- **Room thermostat control** with external sensors
- **PV surplus control** for solar power integration
- **Centralized filtering and disabling of registers**
- **Automatic YAML config for advanced options**
- **Debug logging and troubleshooting tools**
- **Counters for heat pump cycling by operating mode**
- **Unified entity naming convention**
- **Automatic entity migration with conflict resolution**

## ⚙️ Initial Configuration

When setting up the integration, you will need to provide:

- **Name**: A name for your Lambda Heat Pump installation (e.g., "EU08L")
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Number of devices**: Configure how many of each device type you have:
  - Heat Pumps (1-3)
  - Boilers (0-5)
  - Heating Circuits (0-12)
  - Buffers (0-5)
  - Solar Systems (0-2)
- **Firmware Version**: Select your Lambda controller's firmware version

## 🔧 Integration Options

After initial setup, you can modify additional settings in the integration options:

1. Go to Configuration → Integrations
2. Find your Lambda Heat Pump integration and click "Configure"
3. Here you can adjust:
   - Hot water temperature range (min/max)
   - Heating circuit temperature range (min/max)
   - Temperature step size
   - Room thermostat control (using external sensors)
   - PV power sensor as input for PV surplus configuration → see documentation before enabling this feature

## 🌞 PV Surplus Control

The integration supports controlling the heat pump based on available PV surplus. This feature allows the heat pump to utilize excess solar power.

### Features:
- **PV Surplus Detection**: Automatic monitoring of PV power output
- **Modbus Register 102**: Writing current PV power in watts
- **Configurable Sensors**: Selection of any PV power sensors
- **Automatic Updates**: Regular writing of PV data (default: every 10 seconds)
- **Unit Conversion**: Automatic conversion from kW to W

### Configuration:
1. **Enable PV Surplus**: Activate "PV Surplus" in integration options
2. **Select PV Sensor**: Choose a PV power sensor (e.g., template sensor for PV surplus)
3. **Adjust Interval**: Configure the write interval in options

### Supported Sensors:
- **Watt Sensors**: Direct usage (e.g., 1500 W)
- **Kilowatt Sensors**: Automatic conversion (e.g., 1.5 kW → 1500 W)
- **Template Sensors**: For complex PV surplus calculations

### Modbus Register:
- **Register 102**: E-Manager Actual Power (global register)
- **Value Range**: -32768 to 32767 (int16)
- **Unit**: Watts

## 🛠️ Troubleshooting & Support

- **Log Analysis**: Enable debug logging for detailed error output
- **Common Issues**: See troubleshooting section below
- **Support:**
  - [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
  - [Home Assistant Community](https://community.home-assistant.io/)

## 📚 Documentation

- [English Guide](docs/lambda_heat_pumps_en.md)
- [Troubleshooting](docs/lambda_heat_pumps_troubleshooting.md)
- [Modbus Register (EN)](docs/lambda_heat_pumps_modbus_register_en.md)

## 📄 License

MIT License. Use at your own risk. See [LICENSE](LICENSE).

---

# 🇩🇪 Deutsch

## 🚀 Schnelleinstieg

> **HACS Custom Integration**  
> Diese Integration verbindet Lambda Wärmepumpen mit Home Assistant via Modbus/TCP.

### HACS Installation
1. **HACS installieren** (falls noch nicht geschehen)
2. **Custom Repository hinzufügen:**
   - HACS → Integrations → „⋮" → „Custom repositories"
   - URL: `GuidoJeuken-6512/lambda_wp_hacs` (Kategorie: Integration)
3. **Integration suchen & installieren:**
   - „Lambda Heat Pumps" auswählen und installieren
   - Home Assistant neu starten

## ✨ Features

- **Vollständige Modbus/TCP Integration** für Lambda Wärmepumpen
- **Dynamische Sensor/Entity-Erkennung** basierend auf Firmware
- **Konfigurierbare Anzahl von Geräten** (Wärmepumpen, Kessel, Heizkreise, Pufferspeicher, Solarmodule)
- **Raumthermostat-Steuerung** mit externen Sensoren
- **PV-Überschuss-Steuerung** für Solarstrom-Integration
- **Zentrale Filterung und Deaktivierung von Registern**
- **Automatische YAML-Konfiguration für erweiterte Optionen**
- **Debug-Logging und Troubleshooting-Tools**
- **Zähler für Wärmepumpen-Taktung nach Betriebsart**

## ⚙️ Initial Configuration

When setting up the integration, you will need to provide:

- **Name**: A name for your Lambda Heat Pump installation (e.g., "Main Heat Pump")
- **Host**: IP address or hostname of your Lambda controller
- **Port**: Modbus TCP port (default: 502)
- **Slave ID**: Modbus Slave ID (default: 1)
- **Number of devices**: Configure how many of each device type you have:
  - Heat Pumps (1-3)
  - Boilers (0-5)
  - Heating Circuits (0-12)
  - Buffers (0-5)
  - Solar Systems (0-2)
- **Firmware Version**: Select your Lambda controller's firmware version

## 🔧 Integration Options

After initial setup, you can modify additional settings in the integration options:

1. Go to Configuration → Integrations
2. Find your Lambda Heat Pump integration and click "Configure"
3. Here you can adjust:
   - Hot water temperature range (min/max)
   - Heating circuit temperature range (min/max)
   - Temperature step size
   - Room thermostat control (using external sensors)
   - PV power sensor as input for PV surplus configuration → siehe Dokumentation vor Aktivierung

## 🌞 PV-Überschuss-Steuerung

Die Integration unterstützt die Steuerung der Wärmepumpe basierend auf verfügbarem PV-Überschuss. Diese Funktion ermöglicht es der Wärmepumpe, überschüssigen Solarstrom zu nutzen.

### Funktionen:
- **PV-Überschuss-Erkennung**: Automatische Überwachung der PV-Leistung
- **Modbus-Register 102**: Schreiben der aktuellen PV-Leistung in Watt
- **Konfigurierbare Sensoren**: Auswahl beliebiger PV-Leistungssensoren
- **Automatische Aktualisierung**: Regelmäßiges Schreiben der PV-Daten (standardmäßig alle 10 Sekunden)
- **Einheitenkonvertierung**: Automatische Umrechnung von kW in W

### Konfiguration:
1. **PV-Überschuss aktivieren**: In den Integration-Optionen "PV-Überschuss" aktivieren
2. **PV-Sensor auswählen**: Einen PV-Leistungssensor auswählen (z.B. Template-Sensor für PV-Überschuss)
3. **Intervall anpassen**: Das Schreibintervall in den Optionen konfigurieren

### Unterstützte Sensoren:
- **Watt-Sensoren**: Direkte Verwendung (z.B. 1500 W)
- **Kilowatt-Sensoren**: Automatische Umrechnung (z.B. 1.5 kW → 1500 W)
- **Template-Sensoren**: Für komplexe PV-Überschuss-Berechnungen

### Modbus-Register:
- **Register 102**: E-Manager Actual Power (globales Register)
- **Wertebereich**: -32768 bis 32767 (int16)
- **Einheit**: Watt

## 🛠️ Troubleshooting & Support

- **Log-Analyse**: Aktiviere Debug-Logging für detaillierte Fehlerausgabe
- **Häufige Probleme**: Siehe Abschnitt „Troubleshooting" unten
- **Support:**
  - [GitHub Issues](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/issues)
  - [Home Assistant Community](https://community.home-assistant.io/)

## 📚 Weitere Dokumentation

- [Quick Start (DE)](docs/lambda_heat_pumps_quick_start.md)
- [FAQ (DE)](docs/lambda_heat_pumps_faq.md)
- [Entwickler-Guide](docs/lambda_heat_pumps_developer_guide.md)
- [Modbus Register (DE)](docs/lambda_heat_pumps_modbus_register_de.md)
- [Troubleshooting](docs/lambda_heat_pumps_troubleshooting.md)
- [HACS Publishing Guide](docs/lambda_heat_pumps_hacs_publishing.md)

## 📄 Lizenz & Haftung

MIT License. Nutzung auf eigene Gefahr. Siehe [LICENSE](LICENSE).

---

## 📝 Changelog

Siehe [Releases](https://github.com/GuidoJeuken-6512/lambda_wp_hacs/releases) für Änderungen und Breaking Changes.

---

**Developed with ❤️ for the Home Assistant Community**
