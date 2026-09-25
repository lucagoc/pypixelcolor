import logging
import blurhash
import io
import random
import math
from typing import Optional
from .send_image import send_image_hex
from ..lib.device_info import DeviceInfo


def randhash(device_info: Optional[DeviceInfo] = None, save_slot: int = 0):
    """
    Generate a random blurhash image and send it to the device.

    Args:
        device_info: Device information (injected automatically by DeviceSession).
        save_slot: If >= 1, will save to that slot.

    Note:
        The generated image is forwarded as hex_png to send_image_hex().
    """
    rh = _randomHash()
    logging.info(f"random hash: {rh}")
    img = blurhash.decode(rh, device_info.width, device_info.height)
    bytes_io = io.BytesIO()
    img.save(bytes_io, format='PNG')
    img_bytes = bytes_io.getvalue()
    png_hex = img_bytes.hex()
    return send_image_hex(png_hex, 'PNG', device_info=device_info, save_slot=save_slot)


DIGIT_CHARACTERS = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F",
    "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V",
    "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
    "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "#", "$",
    "%", "*", "+", ",", "-", ".", ":", ";", "=", "?", "@", "[", "]", "^", "_", "{",
    "|", "}", "~"
]


def _randomHash() -> str:
    blurhash = DIGIT_CHARACTERS[random.randint(0, len(DIGIT_CHARACTERS)-1)]

    sizeFlag = _decode83(blurhash[0])
    numY = math.floor(sizeFlag / 9) + 1
    numX = (sizeFlag % 9) + 1
    wanted = 4 + 2 * numX * numY

    while len(blurhash) < wanted:
        blurhash += DIGIT_CHARACTERS[random.randint(
            0, len(DIGIT_CHARACTERS)-1)]

    return blurhash


def _decode83(str):
    value = 0
    for c in str:
        digit = DIGIT_CHARACTERS.index(c)
        value = value * 83 + digit
    return value
