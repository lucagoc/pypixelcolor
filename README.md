# pypixelcolor

![pypixelcolor](https://raw.githubusercontent.com/lucagoc/pypixelcolor/refs/heads/main/.github/readme/banner.png)

[![PyPI](https://img.shields.io/pypi/v/pypixelcolor.svg)](https://pypi.org/project/pypixelcolor)
[![AUR version](https://img.shields.io/aur/version/python-pypixelcolor?color=1793d1&logo=arch-linux)](https://aur.archlinux.org/packages/python-pypixelcolor)
[![AUR git version](https://img.shields.io/aur/version/python-pypixelcolor-git?color=1793d1&label=aur-git&logo=arch-linux)](https://aur.archlinux.org/packages/python-pypixelcolor-git)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Build Status](https://github.com/lucagoc/pypixelcolor/actions/workflows/python-app.yml/badge.svg)](https://github.com/lucagoc/pypixelcolor/actions)
[![Publish Status](https://github.com/lucagoc/pypixelcolor/actions/workflows/python-publish.yml/badge.svg)](https://github.com/lucagoc/pypixelcolor/actions)
[![GitHub stars](https://img.shields.io/github/stars/lucagoc/pypixelcolor?style=social)](https://github.com/lucagoc/pypixelcolor/stargazers)

`pypixelcolor` (also known as `iPixel-CLI`) is a Python library and CLI tool for controlling iPixel Color LED matrix devices via Bluetooth Low Energy. It allows you to send commands to the device to manipulate the LED display, retrieve device information, and more.

## Features

- 📝 **Send text**: Display custom messages with various fonts and animations.
- 🖼️ **Send images**: Display images and GIFs on the matrix.
- ⚙️ **Control settings**: Adjust brightness, orientation, and power.
- ⏰ **Clock mode**: Display time with various clock faces.
- 🐍 **Scriptable**: Full Python library support for automation.
- 🖥️ **CLI**: Easy to use command-line interface.

## Installation

### PyPI

```bash
pip install pypixelcolor
```

### Arch Linux (AUR)

Stable version:
```bash
paru -S python-pypixelcolor
# or: yay -S python-pypixelcolor
```

Development version (Git):
```bash
paru -S python-pypixelcolor-git
# or: yay -S python-pypixelcolor-git
```

Check the [Wiki](https://lucagoc.github.io/pypixelcolor/main) for more detailed usage instructions.

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

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/lucagoc/pypixelcolor/blob/main/LICENSE.md) file for details.

This project is not affiliated with or endorsed by the original manufacturer of the iPixel devices or the official "iPixel Color" app.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.
To get started on how to dump BLE logs from an Android device, refer to the [How to get BLE logs](https://github.com/lucagoc/pypixelcolor/wiki/Tutorials#getting-ble-logs-from-an-android-device) guide.
