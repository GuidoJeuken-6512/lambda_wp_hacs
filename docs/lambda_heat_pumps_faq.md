# Lambda Heat Pumps - Frequently Asked Questions

## General Questions

### What is the Lambda Heat Pumps integration?
The Lambda Heat Pumps integration is a custom component for Home Assistant that allows you to monitor and control Lambda heat pump systems via Modbus TCP.

### Which Lambda models are supported?
The integration supports all Lambda heat pump systems that provide Modbus TCP access, including systems with multiple heat pumps, boilers, heating circuits, buffers, and solar components.

### How often is data updated from my Lambda system?
By default, the integration polls data every 30 seconds. You can adjust this interval in the integration options if needed.

### Do I need any additional hardware?
No additional hardware is required if your Lambda controller already has network connectivity and Modbus TCP enabled. The integration communicates directly with the controller over your local network.

## Setup and Configuration

### How do I install the integration?
Copy the `lambda_heat_pumps` folder to your Home Assistant `custom_components` directory, restart Home Assistant, then add the integration through the UI under Configuration → Integrations.

### How do I know how many heating circuits, boilers, etc. to configure?
Configure the number of devices based on your actual Lambda system setup. You can find this information in your Lambda controller configuration or installation documentation. Setting incorrect device counts may result in missing entities or errors.

### Which firmware version should I select?
Select the firmware version that matches your Lambda controller. If unsure, check the controller's system information screen or contact your installer.

### Can I change the configuration after initial setup?
Yes, most settings can be adjusted through the integration options after setup. You can access these by clicking on the "Configure" button for the integration in the Integrations page.

## Features and Functionality

### Can I control room temperature with the integration?
Yes, the integration provides climate entities for heating circuits that allow you to set target temperatures and operating modes.

### How do I use my own room temperature sensors instead of the built-in ones?
Use the `lambda_heat_pumps.update_room_temperature` service to periodically update room temperature readings from your preferred temperature sensors to the Lambda controller.

### Can I control hot water temperature?
Yes, boilers are exposed as climate entities that allow you to set the target hot water temperature within the allowed range.

### Do all sensors update in real-time?
The integration polls data at regular intervals (default: 30 seconds), so there may be a small delay between a change in the system and the update in Home Assistant.

### Can I use this integration in automations?
Yes, all entities and services provided by the integration can be used in Home Assistant automations, scripts, and scenes.

## Troubleshooting

### Why do some entities show "unavailable"?
Entities may show as unavailable if:
- The corresponding device doesn't exist in your system
- There's a communication issue with the Lambda controller
- The data for that entity is not available in the current system state

### Why do climate entities show incorrect modes?
The available modes depend on the operating state of the device and the firmware version. Make sure you've selected the correct firmware version during setup.

### How can I debug communication issues?
Enable debug logging for the integration by adding the following to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.lambda_heat_pumps: debug
```

### What should I do if I get timeout errors?
Network timeouts can occur if there are connectivity issues between Home Assistant and the Lambda controller. Check your network setup and try increasing the polling interval in the integration options.

## Developer Issues

### I'm getting "Python Jedi server crashed" errors in VS Code. How can I fix this?
This error occurs when the Python language server (Jedi) crashes repeatedly in VS Code. To resolve it:

1. **Restart VS Code**: Close and reopen VS Code completely
2. **Check Python Extensions**: Make sure your Python extension is up-to-date
3. **Reset VS Code Python Settings**:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type and select "Python: Select Interpreter"
   - Choose your Python interpreter again
4. **Create/Update settings.json**:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type and select "Preferences: Open Settings (JSON)"
   - Add or update these settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.jediEnabled": false,
     "python.languageServer": "Pylance",
     "python.analysis.extraPaths": [
       "${workspaceFolder}"
     ]
   }
   ```
5. **Check Memory Usage**: If the server crashes persist, your system might be low on memory. Close other applications to free up resources.

### How do I set up a development environment for working on the integration?

1. **Clone the repository**:
   ```bash
   git clone https://github.com/GuidoJeuken-6512/lambda_heat_pumps_hacs
   ```

2. **Set up a virtual environment**:
   ```bash
   cd lambda_heat_pumps_hacs
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements_test.txt
   ```

3. **Run the tests**:
   ```bash
   pytest
   ```

4. **Development workflow**:
   - Make your changes
   - Run `pytest` to verify your changes don't break existing functionality
   - Submit a pull request with your improvements

### How can I debug the integration during development?

1. **Enable debug logging** in your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.lambda_heat_pumps: debug
   ```

2. **Use Visual Studio Code Debug Configuration**:
   - Use the included `.vscode/launch.json` configuration for debugging
   - Set breakpoints in your code
   - Use the Debug Console to examine variables

3. **Log to a file** for persistent debugging:
   ```python
   import logging
   _LOGGER = logging.getLogger(__name__)
   _LOGGER.debug("Debug message with variable: %s", variable)
   ```

## Advanced Topics

### Can I extend the integration to support additional features?
Yes, the integration is designed to be extensible. See the developer guide for information on how to modify or extend the integration.

### How can I contribute to the integration?
Contributions are welcome! You can contribute by submitting pull requests to the GitHub repository with bug fixes, enhancements, or documentation improvements.

### Is the integration compatible with Home Assistant Energy Dashboard?
The integration provides power consumption sensors that can be used in the Energy Dashboard. Look for sensors with names like `sensor.[name]_hpX_fi_power_consumption` which represent the power consumption of individual heat pumps.

## HACS Integration

### How do I publish my integration to HACS?
Publishing to HACS requires several steps:

1. **Prepare your repository**:
   - Ensure your GitHub repository is public
   - Follow the [HACS integration requirements](https://hacs.xyz/docs/publish/integration)
   - Include all required files (README.md, info.md, hacs.json)

2. **Validate your integration**:
   - Use the [HACS Validation GitHub Action](https://github.com/hacs/action)
   - Fix any issues reported by the validator

3. **Submit for inclusion**:
   - Fork the [HACS default repository](https://github.com/hacs/default)
   - Add your integration to the `integration` file
   - Create a pull request with proper documentation

See the detailed guide in our [developer documentation](/home/guido/Dokumente/dockers/config/docs/lambda_heat_pumps_developer_guide.md) for step-by-step instructions.

### What requirements does HACS have for integrations?
HACS has specific requirements including:

- Repository structure following Home Assistant custom integration standards
- Required files: README.md, info.md (or README used as info), hacs.json
- Proper version handling (preferably using releases/tags)
- Documentation on installation and configuration
- Working code that follows Home Assistant best practices
- Validation using HACS validation tools

### Can users install my integration directly from HACS?
Once approved and included in the HACS default repository, users can install your integration directly from the HACS interface. They simply need to:

1. Open HACS in their Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button
4. Search for "Lambda Heat Pumps"
5. Click "Download"

For installation before official inclusion, users can add your repository as a custom repository in HACS.
