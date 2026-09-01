from typing import Union

from ..lib.transport.send_plan import SendPlan, single_window_plan


def _parse_score(score: Union[int, str], name: str) -> int:
    """Validate and convert score to an integer between 0 and 99."""
    if isinstance(score, bool):
        raise ValueError(f"Invalid {name}: boolean values are not allowed.")

    try:
        val = int(score)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid {name}: {score!r}. Expected an integer between 0 and 99.")

    if not (0 <= val <= 99):
        raise ValueError(f"{name} must be between 0 and 99, got {val}.")

    return val


def set_scores(score_p1: Union[int, str] = 0, score_p2: Union[int, str] = 0) -> SendPlan:
    """
    Set scoreboard scores for player 1 and player 2.

    Args:
        score_p1 (Union[int, str]): Score for player 1 (0-99). Defaults to 0.
        score_p2 (Union[int, str]): Score for player 2 (0-99). Defaults to 0.

    Returns:
        SendPlan: The single window send plan for this command.
    """
    p1 = _parse_score(score_p1, "score_p1")
    p2 = _parse_score(score_p2, "score_p2")

    payload = bytes([
        8,      # Command length
        0,      # Reserved
        0x0A,   # Command ID
        0x80,   # Command type ID
        p1,     # Player 1 score
        0,      # Padding
        p2,     # Player 2 score
        0       # Padding
    ])
    return single_window_plan("set_scores", payload)
