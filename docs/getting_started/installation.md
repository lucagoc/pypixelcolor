# Installation

## Prerequisites

Before installing `pypixelcolor`, ensure you have the following prerequisites:

- Python 3.9 or higher
- pip (Python package installer)
- Bluetooth adapter on your machine

## Installation

### Via PyPI (pip)

You can install `pypixelcolor` using pip:

```bash
pip install pypixelcolor
```

To enable additional image format support such as HEIF/HEIC (using `pillow-heif`), install with the `extra` option:

```bash
pip install "pypixelcolor[extra]"
```

To verify that the installation was successful, you can check the installed version:

```bash
pypixelcolor --version
```

### Via Arch Linux (AUR)

If you are using Arch Linux or an Arch-based distribution, `pypixelcolor` is available on the [AUR](https://aur.archlinux.org/packages/python-pypixelcolor):

**Stable release:**

```bash
paru -S python-pypixelcolor
```

**Development version (latest Git main):**

```bash
paru -S python-pypixelcolor-git
```

## Installation from source

If you prefer to install `pypixelcolor` from the source code, follow these steps:

- Clone the repository from GitHub:

  ```bash
  git clone https://github.com/lucagoc/pypixelcolor.git
  ```

- Navigate to the cloned directory:

  ```bash
  cd pypixelcolor
  ```

- Install the package using pip:

  ```bash
  pip install .
  ```

## Post-installation

After installation, you may want to set up your Bluetooth adapter to ensure it works correctly with `pypixelcolor`. Make sure your Bluetooth is enabled and that your device is discoverable.
You can now start using `pypixelcolor` to control your iPixel Color LED matrix devices!

[Using CLI](cli.md){ .md-button .md-button--primary }
[Using WebSocket](websocket.md){ .md-button .md-button--primary }
[Using Python library](library.md){ .md-button .md-button--primary }