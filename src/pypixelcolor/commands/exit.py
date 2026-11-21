from typing import Any

from ..lib.transport.send_plan import SendPlan, single_window_plan


def exit_cmd() -> SendPlan:
    """Exit / leave the current screen (return to the saved-slot playlist).

    Bytes: `[4, 0, 1, 1]`.

    Returns:
        A SendPlan wrapping the exact exit command bytes.
    """
    cmd = bytes([4, 0, 1, 1])
    # Exit is a display/playlist operation; the device does not emit a notify ACK
    # for it (unlike stream commands), so we don't wait for one.
    return single_window_plan("exit", cmd, requires_ack=False)
