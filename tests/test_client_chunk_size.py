"""Public chunk-size configuration with real builders/send loop and synthetic GATT."""

import asyncio
import atexit
from io import BytesIO
import random
from types import SimpleNamespace

from PIL import Image
import pytest
from bleak.exc import BleakCharacteristicNotFoundError

from pypixelcolor import AsyncClient, Client
from pypixelcolor.commands.send_image import send_image_hex
from pypixelcolor.lib.device_session import DeviceSession
from pypixelcolor.lib.transport.ack_manager import AckManager
from pypixelcolor.lib.transport.send_plan import single_window_plan


def image_bytes():
    output = BytesIO()
    Image.frombytes('RGB', (64, 16), random.Random(42).randbytes(64 * 16 * 3)).save(output, format='PNG')
    return output.getvalue()


class Gatt:
    def __init__(self, ack, expected, maximum):
        self.ack, self.expected = ack, expected
        self.writes = []
        self.characteristic = SimpleNamespace(max_write_without_response_size=maximum)
        self.services = SimpleNamespace(get_characteristic=lambda _: self.characteristic)

    async def write_gatt_char(self, _, data, *, response):
        self.writes.append((bytes(data), response))
        if sum(len(chunk) for chunk, _ in self.writes) == len(self.expected):
            self.ack.window_event.set()
            self.ack.all_event.set()

    async def stop_notify(self, _):
        pass

    async def disconnect(self):
        pass


def connected(client, expected, maximum=244):
    ack = AckManager()
    raw = Gatt(ack, expected, maximum)
    client._connected = True
    client._session._connected = True
    client._session._client = raw
    client._session._ack_mgr = ack
    return raw


@pytest.mark.parametrize('chunk_size,response,maximum,expected_size', [
    (None, True, 20, 244),
    (500, True, 20, 500),
    (512, True, 20, 512),
    (500, False, 100, 100),
    (500, False, 514, 500),
    (20, False, 100, 20),
])
def test_public_async_image_upload_preserves_payload_and_respects_chunk_policy(chunk_size, response, maximum, expected_size):
    png = image_bytes()
    expected = send_image_hex(png.hex(), '.png').windows[0].data
    client = AsyncClient('mock', write_with_response=response, chunk_size=chunk_size)
    raw = connected(client, expected, maximum)
    asyncio.run(client.send_image_hex(png.hex(), '.png'))
    assert b''.join(chunk for chunk, _ in raw.writes) == expected
    assert max(len(chunk) for chunk, _ in raw.writes) == expected_size
    assert all(flag is response for _, flag in raw.writes)


def test_public_sync_image_upload_uses_the_requested_chunk_size():
    png = image_bytes()
    expected = send_image_hex(png.hex(), '.png').windows[0].data
    client = Client('mock', chunk_size=500)
    try:
        raw = connected(client._async_client, expected)
        client.send_image_hex(png.hex(), '.png')
        assert b''.join(chunk for chunk, _ in raw.writes) == expected
        assert max(len(chunk) for chunk, _ in raw.writes) == 500
        client.disconnect()
    finally:
        client._cleanup_on_exit()
        client._loop_thread.join(timeout=1)
        assert not client._loop_thread.is_alive()
        client._loop.close()
        atexit.unregister(client._cleanup_on_exit)


@pytest.mark.parametrize('factory', [DeviceSession, AsyncClient, Client])
@pytest.mark.parametrize('size', [0, -1, 513, True, 1.5, '500'])
def test_invalid_chunk_size_is_rejected_by_public_constructors(factory, size):
    with pytest.raises(ValueError, match='chunk_size'):
        factory('mock', chunk_size=size)


def test_unset_override_preserves_a_command_specific_chunk_size():
    session = DeviceSession('mock')
    session._connected = True
    session._ack_mgr = AckManager()
    expected = bytes(range(128))
    raw = session._client = Gatt(session._ack_mgr, expected, 244)
    asyncio.run(session.execute_command(lambda: single_window_plan('custom', expected, chunk_size=32)))
    assert [len(chunk) for chunk, _ in raw.writes] == [32, 32, 32, 32]


@pytest.mark.parametrize('maximum', [0, None])
def test_unusable_without_response_characteristic_fails_before_writing(maximum):
    client = AsyncClient('mock', write_with_response=False, chunk_size=500)
    raw = connected(client, b'')
    if maximum is None:
        raw.characteristic = None
        error = BleakCharacteristicNotFoundError
    else:
        raw.characteristic.max_write_without_response_size = maximum
        error = ValueError
    with pytest.raises(error):
        asyncio.run(client.send_image_hex(image_bytes().hex(), '.png'))
    assert raw.writes == []
