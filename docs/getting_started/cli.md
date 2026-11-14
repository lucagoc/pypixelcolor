# Getting started with CLI

## Scanning for devices

Find your device's MAC address by scanning for nearby Bluetooth devices:

```bash
pypixelcolor --scan
```

<video controls width="100%" preload="metadata">
      <source src="../assets/videos/scan.webm" type="video/mp4">
      Your browser doesn't support videos.
    </video>

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

For more information on available commands, refer to the [Commands](../commands/content.md) page.

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



## Faster uploads

`--fast` writes BLE chunks without response and relies on the device's per-window
acknowledgements. Image and GIF uploads get several times faster:

```bash
pypixelcolor -a <MAC_ADDRESS> --fast -c send_image animation.gif
```
