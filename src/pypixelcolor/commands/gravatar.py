import logging
from libgravatar import Gravatar
import requests
from typing import Optional
from .send_image import send_image_hex
from ..lib.device_info import DeviceInfo


def gravatar(email: str, device_info: Optional[DeviceInfo] = None, save_slot: int = 0):
    """
    Fetch a gravatar icon and send it to the device.

    Args:
        email: the mail address for the gravatar to fetch
        device_info: Device information (injected automatically by DeviceSession).
        save_slot: If >= 1, will save to that slot.

    Note:
        The fetched image is forwarded as hex_png to send_image_hex().
    """
    g = Gravatar(email)
    url = g.get_image(size=device_info.width)
    logging.info(f"fetching from: {url}")
    resp = requests.get(url)
    if resp.status_code == 200:
        png_hex = resp.content.hex()
        return send_image_hex(png_hex, 'PNG', device_info=device_info, save_slot=save_slot)
    else:
        logging.info(f"Request failed: {resp.status_code}")
