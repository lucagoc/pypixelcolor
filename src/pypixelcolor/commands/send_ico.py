from icoextract import IconExtractor, IconExtractorError
from PIL import Image
import io
from typing import Optional
from .send_image import send_image_hex
from ..lib.device_info import DeviceInfo


def send_ico(fname: str, index: int = 0, device_info: Optional[DeviceInfo] = None, save_slot: int = 0):
    """
    Extract an ICO from a file and send it to the device.

    Args:
        fname: a filename
        index: icon index to extract
        device_info: Device information (injected automatically by DeviceSession).
        save_slot: If >= 1, will save to that slot.

    Note:
        The extracted image is forwarded as hex_png to send_image_hex().
    """
    extractor = IconExtractor(fname)
    ico_list = extractor.list_group_icons()
    data = extractor.get_icon(resource_id=ico_list[int(index)][0])
    img = Image.open(data)
    size = device_info.width, device_info.height
    img.thumbnail(size, Image.Resampling.LANCZOS)
    bytes_io = io.BytesIO()
    img.save(bytes_io, format='PNG')
    img_bytes = bytes_io.getvalue()
    png_hex = img_bytes.hex()
    return send_image_hex(png_hex, 'PNG', device_info=device_info, save_slot=save_slot)
