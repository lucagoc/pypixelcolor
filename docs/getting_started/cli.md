# Getting started with CLI

## Scanning for devices

Find your device's MAC address by scanning for nearby Bluetooth devices:

```bash
pypixelcolor --scan
```

![Scan for devices](../assets/gifs/scan.gif)

If your device is found, take note of its MAC address (e.g., `30:E1:AF:BD:5F:D0`).

```txt
% pypixelcolor --scan
[INFO] Scanning for Bluetooth devices...
[OK] Found 1 LED device(s):
  - LED_BLE_E1BD5C80 (30:E1:AF:BD:5F:D0)
```

> If your device is not found, ensure it is powered, in range and not connected to another device.

See [troubleshooting](../troubleshooting/bluetooth_connection.md) for more help.

## Sending a command

CLI commands are sent using the `-c` option, along with the `-a` or `--address` option to specify the target device's MAC address.

For instance, to send a text message to your device, use the following command, replacing the MAC address with your device's MAC address:

```bash
pypixelcolor -a <MAC_ADDRESS> -c send_text "Hello pypixelcolor"
```

You can also use inline color tags and specify custom parameters or fonts:

```bash
# Send multi-colored text
pypixelcolor -a <MAC_ADDRESS> -c send_text "[#ff0000]Hello[/] [#00ff00]pypixelcolor[/]"

# Send text using a custom Font
pypixelcolor -a <MAC_ADDRESS> -c send_text "Hello" font="Press Start 2P" animation=1 speed=100
```

You can also control timers or update scoreboard scores:

```bash
# Start or pause the timer
pypixelcolor -a <MAC_ADDRESS> -c set_timer start
pypixelcolor -a <MAC_ADDRESS> -c set_timer pause
pypixelcolor -a <MAC_ADDRESS> -c set_timer stop

# Set scores for player 1 and player 2
pypixelcolor -a <MAC_ADDRESS> -c set_scores score_p1=10 score_p2=7
```

For more information on available commands, refer to the [Commands](../commands/content.md) page.

## Interactive Font Configuration TUI

`pypixelcolor` includes a built-in terminal user interface (TUI) to preview and calibrate fonts for the commmand `send_text`:

```bash
pypixelcolor --font-config
```

This interface allows you to preview rendering across 16px, 24px, and 32px heights, adjust font sizes, offsets, pixel threshold, toggle variable-width mode, and save preferences.

## Logging and Troubleshooting

By default in an interactive terminal, `pypixelcolor` shows a clean status spinner. If you want detailed logs or are troubleshooting an issue, you can specify `--loglevel`:

```bash
# Show debug logs and full traceback on error
pypixelcolor -a <MAC_ADDRESS> -c get_device_info --loglevel DEBUG
```

## Advanced usage

You can execute multiple commands in a single call. For example, to clear the display, set the brightness to 50, and switch to clock mode, you can run:

```bash
pypixelcolor -a <MAC_ADDRESS> -c clear -c set_brightness 50 -c set_clock_mode
```


