# Getting BLE logs from an Android device

## Requirements

- An Android device with Bluetooth capabilities
- [adb](https://developer.android.com/tools/releases/platform-tools) (Android Debug Bridge) installed on your computer
- USB cable to connect the Android device to your computer (or Wifi for wireless setup)
- [Wireshark](https://www.wireshark.org/) if you want to analyze the logs

## Step-by-step guide

Before you start capturing BLE logs, you need to prepare your Android device.

### Enable USB debugging on your Android device

- Go to **Settings** > **About phone**.
- Tap on **Build number** 7 times to enable Developer options.
- Go back to **Settings** > **Developer options** and enable **USB debugging**.

*Steps may vary slightly depending on your Android version and device manufacturer.*

### Enable Bluetooth HCI snoop log on your Android device

Go to **Settings** > **Developer options**.
Scroll down and set **Bluetooth HCI snoop log** to **Enabled**.
Restart the bluetooth service by toggling Bluetooth off and then on again.

You can now do actions on your Android device that will generate BLE logs.

### Capture the BLE logs

When you are done, follow these steps to retrieve the logs:

1. **Connect your Android device** to your computer using a USB cable or ensure you have a wireless ADB setup.
2. **Open a terminal** or command prompt on your computer.
3. **Check if your device is connected** by running:

   ```bash
   adb devices
   ```

   You should see your device listed.

   *If you see "unauthorized", make sure to accept the USB debugging prompt on your Android device.*
4. **Generate a bugreport** from your device by running:

   ```bash
   adb bugreport 
   ```

   This command will create a zip file containing various logs, including the Bluetooth HCI snoop log.
   The zip file will be saved in the current directory with a name like `bugreport-<device_name>-<timestamp>.zip`.
5. **Extract the log** from the bug report by unzipping `FS/data/misc/bluetooth/logs/btsnoop_hci_<date>_<time>.log`.
    If you only have a file named `btsnooz_hci.log`, data sent to BLE devices has been filtered from logging, make sure you set Bluetooth HCI snoop log to **Enabled** and restart your device.

6. **Analyze the log file**:
   - You can open the `btsnoop_hci.log` file in Wireshark for analysis.
   - In Wireshark, go to **File** > **Open** and select the `btsnoop_hci.log` file.
   - Protip: use filter `(btatt.opcode.method == 0x12)` to only view write requests sent to BLE devices.
