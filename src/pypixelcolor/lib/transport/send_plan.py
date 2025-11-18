import asyncio
from dataclasses import dataclass, field
from typing import Iterable, Callable, Awaitable, Optional, Any
from logging import getLogger

from .ack_manager import AckManager, AckPolicy
from .window import Window
from ..constants import NOTIFY_UUID, WRITE_UUID
from ..command_result import CommandResult

logger = getLogger(__name__)

@dataclass
class SendPlan:
    id: str
    windows: Iterable[Window]
    chunk_size: int = 244
    window_size: int = 12 * 1024
    ack_policy: AckPolicy = field(default_factory=AckPolicy)
    response_handler: Optional[Callable[[Any, bytes], Awaitable[Any]]] = None
    """Optional async function to handle response data. 
    Signature: async def handler(client, response: bytes) -> Any
    If set, the command expects a response from the device."""


def single_window_plan(plan_id: str, data: bytes, *,
                       requires_ack: bool = True,
                       chunk_size: int = 244,
                       window_size: int = 12 * 1024,
                       ack_policy: AckPolicy | None = None,
                       response_handler: Optional[Callable[[Any, bytes], Awaitable[Any]]] = None) -> SendPlan:
    if ack_policy is None:
        ack_policy = AckPolicy(ack_per_window=requires_ack, ack_final=False)
    return SendPlan(
        id=plan_id,
        windows=[Window(data=data, requires_ack=requires_ack)],
        chunk_size=chunk_size,
        window_size=window_size,
        ack_policy=ack_policy,
        response_handler=response_handler,
    )

def _chunk_bytes(buf: bytes, size: int):
    pos = 0
    total = len(buf)
    while pos < total:
        end = min(pos + size, total)
        yield buf[pos:end]
        pos = end

async def send_plan(client, plan: SendPlan, ack_mgr: AckManager, *, write_uuid: str = WRITE_UUID, ack_timeout: float = 8.0) -> CommandResult:
    """
    Send a SendPlan generically.

    - Iterate windows
    - Chunk by plan.chunk_size
    - Wait for ACK per window if required
    - Wait for final ACK if policy requires
    - If response_handler is set, capture and return the response
    
    Returns:
        CommandResult with optional data from response_handler
    """
    logger.info(f"Sending plan '{plan.id}'")
    
    # If this command expects a response, set up response capture
    response_data = None
    response_event = None
    needs_ack_restore = False
    
    if plan.response_handler is not None:
        response_event = asyncio.Event()
        needs_ack_restore = True
        
        # Stop the ack_mgr handler temporarily
        try:
            await client.stop_notify(NOTIFY_UUID)
        except Exception as e:
            logger.debug(f"No existing notification to stop: {e}")
        
        def response_capture_handler(_, data: bytes):
            nonlocal response_data
            logger.debug(f"Captured response for '{plan.id}': {data.hex()}")
            response_data = data
            response_event.set()
        
        # Enable notifications for response
        try:
            await client.start_notify(NOTIFY_UUID, response_capture_handler)
        except Exception as e:
            logger.warning(f"Failed to enable response notifications: {e}")
    
    try:
        # Send the windows
        for idx, win in enumerate(plan.windows):
            ack_mgr.reset()
            # Send this window in chunks
            for chunk in _chunk_bytes(win.data, plan.chunk_size):
                await client.write_gatt_char(write_uuid, chunk, response=True)
            if plan.ack_policy.ack_per_window and win.requires_ack:
                try:
                    await asyncio.wait_for(ack_mgr.window_event.wait(), timeout=ack_timeout)
                except asyncio.TimeoutError:
                    raise RuntimeError("cur12k_no_answer: no ack from device")
        
        if plan.ack_policy.ack_final:
            try:
                await asyncio.wait_for(ack_mgr.all_event.wait(), timeout=ack_timeout)
            except asyncio.TimeoutError:
                raise RuntimeError("cur12k_no_answer: no final ack from device")
        
        # If expecting a response, wait for it
        if plan.response_handler is not None and response_event is not None:
            try:
                await asyncio.wait_for(response_event.wait(), timeout=ack_timeout)
                if response_data is not None:
                    result_data = await plan.response_handler(client, response_data)
                    return CommandResult(success=True, data=result_data)
                else:
                    logger.warning(f"No response data received for '{plan.id}'")
                    return CommandResult(success=False, message="No response data received")
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for response for '{plan.id}'")
                return CommandResult(success=False, message="Timeout waiting for response")
        
        # Standard command without response
        return CommandResult(success=True)
        
    finally:
        # Restore ack_mgr notifications if we temporarily replaced them
        if needs_ack_restore:
            try:
                await client.stop_notify(NOTIFY_UUID)
            except Exception as e:
                logger.debug(f"Failed to stop response notifications: {e}")
            
            # Re-enable ack_mgr notifications
            try:
                await client.start_notify(NOTIFY_UUID, ack_mgr.make_notify_handler())
                logger.debug("Restored ack_mgr notification handler")
            except Exception as e:
                logger.warning(f"Failed to restore ack_mgr notifications: {e}")
