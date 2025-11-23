# pypixelcolor

![pypixelcolor](.github/readme/banner.png)

[![PyPI](https://img.shields.io/pypi/v/pypixelcolor.svg)](https://pypi.org/project/pypixelcolor)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Build Status](https://github.com/lucagoc/pypixelcolor/actions/workflows/python-app.yml/badge.svg)](https://github.com/lucagoc/pypixelcolor/actions)
[![Publish Status](https://github.com/lucagoc/pypixelcolor/actions/workflows/python-publish.yml/badge.svg)](https://github.com/lucagoc/pypixelcolor/actions)

`pypixelcolor` (also known as `iPixel-CLI`) is a Python library and CLI tool for controlling iPixel Color LED matrix devices via Bluetooth Low Energy. It allows you to send commands to the device to manipulate the LED display, retrieve device information, and more.

## Features

- Send text, images
- Control animations and effects
- Retrieve device information
- Scriptable via Python

## Installation

```bash
pip install pypixelcolor
```

## Usage

### CLI

```bash
pypixelcolor --help
```

### Python Library

```python
import pypixelcolor

client = pypixelcolor.Client("BLE_DEVICE_ADDRESS")
client.connect()
client.send_text("Hello, World!")
client.disconnect()
```

### WebSocket server

```bash
python -m pypixelcolor.websocket --help
```

See the [wiki](https://github.com/lucagoc/pypixelcolor/wiki) for more detailed usage instructions.

## Development

This project uses [Hatch](https://hatch.pypa.io/latest/) for packaging and managing the development environment.

### Setup development environment

#### Create and activate the environment

```bash
hatch env create
```

#### Activate the environment

```bash
hatch shell
```

#### Install the package in editable mode

```bash
hatch run pip install -e '.[dev]'
```

#### Run tests

```bash
hatch run pytest
```

#### Build package

```bash
hatch build
```

## Related projects

- [iPixel-CFW](https://github.com/lucagoc/iPixel-CFW): CFW experimentation
- [iPixel-ESPHome](https://github.com/lucagoc/iPixel-ESPHome): ESPHome integration

Check also these cool projects made by other developers:

- [iPixel-ESP32 (ToBiDi0410)](https://github.com/ToBiDi0410/iPixel-ESP32): ESP32 port of this project
- [iPixel-CLI-ESP32 (Cino2424)](https://github.com/Cino2424/iPixel-CLI-ESP32/tree/port-esp32): Another ESP32 port of this project
- [go-ipxl (yyewolf)](https://github.com/yyewolf/go-ipxl): Go library implementation

## Other

> 💡 If your terminal doesn't support emojis, you can disable them with the `--noemojis` flag.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.
To get started on how to dump BLE logs from an Android device, refer to the [How to get BLE logs](https://github.com/lucagoc/pypixelcolor/wiki/Tutorials#getting-ble-logs-from-an-android-device) guide.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/lucagoc/pypixelcolor/blob/main/LICENSE.md) file for details.

This project is not affiliated with or endorsed by the original manufacturer of the iPixel devices or the official "iPixel Color" app.
