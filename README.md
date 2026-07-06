# Kodi WiZ Control

A Kodi addon for discovering and controlling WiZ smart lighting and socket devices within Kodi.

## Features

- Discover WiZ devices on the local network
- Store up to 20 WiZ devices in addon settings
- Control device power state (On / Off)
- Adjust brightness, color temperature, and RGB color for supported bulbs/strips
- Launch preconfigured device control flows via Kodi addon settings
- Support for light and socket device icons and room mapping

## Requirements

- Kodi with Python 3 support
- Kodi addon API compatible with `xbmc.python` 3.0 and `xbmc.addon` 20.0
- WiZ devices must be reachable on the local network

## Installation

1. install addon by selecting the zip file, e.g. script.wiz.1.0.3.zip
2. Enable the addon from Kodi's addon browser if needed.

## Version History

- v1.0.3 (2026-07-06)
  - Added unit tests for program controller logic and Wiz module helpers
  - Refactored phase-shifted program execution to use dedicated controllers for each device
- v1.0.2 (2026-07-05)
  - Cleaned up unused translation/message keys in the addon resources
- v1.0.1 (2026-07-04)
  - Added phase-shift support for infinite programs with multiple bulbs
  - Added localized dialog text for English and German
- v1.0.0 (2026-05-10)
  - Initial version

## Usage

1. Open the `WiZ Control` addon from Kodi.
2. If no WiZ devices are configured, the addon will open its settings screen.
3. Use the `scan` action in settings to discover WiZ devices on the network.
4. Select discovered devices to add them to the addon configuration.
5. Run the addon again to control selected WiZ devices.


## Configuration

- Each configured device stores IP address, MAC, name, enabled status, icon, and order.
- Devices can be enabled or disabled independently in settings.
- Device icons may be customized to reflect the device type or room.

## Project Structure

- `script.wiz/addon.py` - addon entrypoint
- `script.wiz/addon.xml` - Kodi addon manifest
- `script.wiz/resources/settings.xml` - addon settings UI
- `script.wiz/resources/lib/` - addon Python library modules

## License

This project is released under the MIT License. See `LICENSE` for details.

