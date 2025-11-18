import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AckPolicy:
    ack_per_window: bool = True
    ack_final: bool = True

class AckManager:
    def __init__(self):
        self.window_event = asyncio.Event()
        self.all_event = asyncio.Event()

    def reset(self):
        self.window_event.clear()
        self.all_event.clear()

    def make_notify_handler(self):
        def handler(_, data: bytes):
            if not data:
                return
            try:
                logger.debug(f"Notify frame: {data.hex()}")
            except Exception:
                pass
            # Protocol: 0x05 ... code in data[4]
            if len(data) == 5 and data[0] == 0x05:
                if data[4] in (0, 1):
                    self.window_event.set()
                elif data[4] == 3:
                    self.window_event.set()
                    self.all_event.set()
                return
            b0 = data[0]
            b4 = data[4] if len(data) > 4 else None
            if b0 == 0x05 and b4 is not None:
                if b4 in (0, 1):
                    self.window_event.set()
                elif b4 == 3:
                    self.window_event.set()
                    self.all_event.set()
        return handler
