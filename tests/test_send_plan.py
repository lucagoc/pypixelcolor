# -*- coding: utf-8 -*-
"""Tests for the send_plan transport: write-with-response vs write-without-response."""

import asyncio

import pytest

from pypixelcolor.lib.transport.ack_manager import AckManager
from pypixelcolor.lib.transport.send_plan import send_plan, single_window_plan


class FakeClient:
    """Records write_gatt_char calls and acks the window after the last chunk."""

    def __init__(self, ack_mgr: AckManager, total_chunks: int):
        self.ack_mgr = ack_mgr
        self.total_chunks = total_chunks
        self.writes = []

    async def write_gatt_char(self, uuid, data, response=True):
        self.writes.append((bytes(data), response))
        if len(self.writes) == self.total_chunks:
            self.ack_mgr.window_event.set()


def _run(write_with_response):
    payload = bytes(range(256)) * 3  # 768 bytes -> 4 chunks of 244
    plan = single_window_plan("test", payload, requires_ack=True, chunk_size=244)
    ack_mgr = AckManager()
    client = FakeClient(ack_mgr, total_chunks=4)
    kwargs = {} if write_with_response is None else {"write_with_response": write_with_response}
    result = asyncio.run(send_plan(client, plan, ack_mgr, **kwargs))
    return client, result


def test_default_writes_with_response():
    client, result = _run(None)
    assert result.success
    assert len(client.writes) == 4
    assert all(resp is True for _, resp in client.writes)
    assert b"".join(d for d, _ in client.writes) == bytes(range(256)) * 3


def test_write_without_response():
    client, result = _run(False)
    assert result.success
    assert len(client.writes) == 4
    assert all(resp is False for _, resp in client.writes)


def test_window_ack_still_required_without_response():
    payload = bytes(300)
    plan = single_window_plan("test", payload, requires_ack=True, chunk_size=244)
    ack_mgr = AckManager()
    client = FakeClient(ack_mgr, total_chunks=99)  # never acks
    with pytest.raises(RuntimeError, match="no ack"):
        asyncio.run(send_plan(client, plan, ack_mgr, write_with_response=False, ack_timeout=0.1))
