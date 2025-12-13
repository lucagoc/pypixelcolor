# Bluetooth Connection Issues

## Device not found

- Ensure the device is powered on.
- Ensure the device is not connected to another phone or computer. The device can only handle one BLE connection at a time.
- Try moving closer to the device.

## Connection Timeout

If you experience timeouts when connecting:

- Restart the Bluetooth service on your computer.
- Power cycle the LED device.

## `pypixelcolor.lib.transport.send_plan` errors with `bleak` 2.0.x

I'm investigating issues with the new version of `bleak` 2.0.x that may cause connection problems on some systems.
See [issue #58](https://github.com/lucagoc/pypixelcolor/issues/58) for more details.

```txt
Failed to enable response notifications: [org.freedesktop.DBus.Error.UnknownObject] Method "AcquireNotify" with signature "a{sv}" on interface "org.bluez.GattCharacteristic1" doesn't exist
```

If you experience persistent connection issues, consider downgrading to `bleak` 1.1.1 as a temporary workaround:

```bash
pip uninstall bleak
pip install bleak==1.1.1
```
