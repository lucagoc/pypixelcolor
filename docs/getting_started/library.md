# Using pypixelcolor as a Python library

## Quickstart Example

All clients and data models can be imported directly from `pypixelcolor` (or `pypixelcolor.models`).

Here is a practical example demonstrating the most common features:

```python
import time
from pypixelcolor import (
    Client,
    TextAnimation,
    TimerAction,
    ResizeMethod,
    FontConfig,
)

MAC_ADDRESS = "30:E1:AF:BD:5F:D0"

# The context manager automatically handles connection and disconnection
with Client(MAC_ADDRESS) as device:
    # 1. Inspect device dimensions and info
    info = device.get_device_info()
    print(f"Connected to {info.width}x{info.height} LED matrix (Type {info.led_type})")

    # 2. Display an image or animated GIF
    device.send_image("./banner.png", resize_method=ResizeMethod.FIT)
    time.sleep(3)

    # 3. Send text with animations, emojis, and inline color tags
    device.send_text(
        "[#ff0000]Hello[/] [#00ff00]pypixelcolor[/] 🚀",
        animation=TextAnimation.SCROLL_LEFT,
        speed=80,
    )
    time.sleep(3)

    # 4. Smooth pulsing text with a custom font
    custom_font = FontConfig.from_file("./fonts/retro.ttf", font_size=16)
    device.send_text("ALERT", font=custom_font, animation=TextAnimation.FADE)
    time.sleep(2)

    # 5. Control stopwatch timer
    device.set_timer(TimerAction.START)
    time.sleep(5)
    device.set_timer(TimerAction.STOP)

    # 6. Clock mode and brightness
    device.set_brightness(60)
    device.set_clock_mode(style=1, format_24=True)
```

## Asynchronous Usage (`AsyncClient`)

For async applications or controlling multiple devices concurrently:

```python
import asyncio
from pypixelcolor import AsyncClient, TextAnimation

async def main():
    async with AsyncClient("30:E1:AF:BD:5F:D0") as device:
        await device.send_text("Hello Async!", animation=TextAnimation.SCROLL_LEFT)

if __name__ == "__main__":
    asyncio.run(main())
```



## Faster uploads

By default every BLE chunk is written "with response", which costs one round trip per
244 bytes. Pass `write_with_response=False` to write chunks without response; the
device still acknowledges each 12 KB window, so transfers stay flow-controlled. On a
64x16 device this made image and GIF uploads about three times faster.

```python
with Client(MAC_ADDRESS, write_with_response=False) as device:
    device.send_image("./animation.gif")
```

The CLI equivalent is `--fast`.
