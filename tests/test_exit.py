# -*- coding: utf-8 -*-
"""Comprehensive tests for the exit command.

Exit / leave the current screen -> return to the saved-slot playlist.
Bytes: `[4, 0, 1, 1]` (no header/CRC framing, sent via sendCompat).

These tests verify EVERY assumption about the exit command:
  1. Byte layout
  2. Command ID 0x0001 = exit/leave
  3. Registration in COMMANDS dict
  4. requires_ack=False (device does NOT notify-ACK display ops)
  5. Consistency with sibling simple commands (clear/delete)
"""

import pytest

from pypixelcolor.commands import COMMANDS
from pypixelcolor.commands.exit import exit_cmd


# --- Assumption 1: Exact byte layout ---

def test_exit_exact_bytes():
    """Exit must emit exactly [4, 0, 1, 1]."""
    plan = exit_cmd()
    assert plan.id == "exit"
    windows = list(plan.windows)
    assert len(windows) == 1
    assert list(windows[0].data) == [4, 0, 1, 1]


def test_exit_byte_layout_semantics():
    """Verify each byte's semantic role: [len_lo, len_hi, cmd, subcmd]."""
    data = bytes(exit_cmd().windows[0].data)
    assert len(data) == 4
    assert data[0] == 4        # length (4 bytes total)
    assert data[1] == 0        # len_hi (length < 256)
    assert data[2] == 1        # command ID 0x0001 = exit/leave
    assert data[3] == 1        # subcommand 1


def test_exit_bytes_immutable_type():
    """Plan data must be a frozen bytes object."""
    data = exit_cmd().windows[0].data
    assert isinstance(data, bytes)
    assert data == b"\x04\x00\x01\x01"


# --- Assumption 2: Command ID and semantics ---

def test_exit_command_id_is_zerox0001():
    """Command ID byte must be 1 (0x0001 = exit/leave)."""
    assert exit_cmd().windows[0].data[2] == 1


def test_exit_does_not_clear_or_blank():
    """Exit returns to playlist; it must NOT erase stored content."""
    # Unlike clear() [4,0,3,0x80] which deletes all ROM data,
    # exit [4,0,1,1] only leaves the current screen.
    clear_bytes = bytes(__import__("pypixelcolor.commands.clear", fromlist=["clear"]).clear().windows[0].data)
    exit_bytes = bytes(exit_cmd().windows[0].data)
    assert clear_bytes != exit_bytes
    # clear has 4 bytes, exit has 4 bytes, but different command IDs
    assert clear_bytes[2] == 3   # clear = cmd 0x0003
    assert exit_bytes[2] == 1    # exit = cmd 0x0001


# --- Assumption 3: Registration ---

def test_exit_registered_in_commands():
    """`exit` must be registered in COMMANDS dict."""
    assert "exit" in COMMANDS
    assert COMMANDS["exit"] is exit_cmd


def test_exit_docstring_mentions_exit():
    """Exit command docstring should describe leaving the screen."""
    doc = exit_cmd.__doc__ or ""
    assert "exit" in doc.lower() or "leave" in doc.lower() or "playlist" in doc.lower()


# --- Assumption 4: ACK policy (display ops don't notify-ACK) ---

def test_exit_requires_ack_false():
    """Exit is a display operation; the device does NOT emit a notify-ACK.
    
    Sibling display commands (set_fun_mode, set_rhythm_mode, set_pixels)
    all use requires_ack=False. Exit must be consistent.
    """
    plan = exit_cmd()
    window = list(plan.windows)[0]
    assert window.requires_ack is False
    # ack_final must also be False (no final ACK for display ops)
    assert plan.ack_policy.ack_final is False


def test_exit_ack_policy_matches_fun_mode():
    """Exit's ACK policy should match set_fun_mode (both are display ops)."""
    from pypixelcolor.commands.set_fun_mode import set_fun_mode
    from pypixelcolor.commands.set_rhythm_mode import set_rhythm_mode, set_rhythm_mode_2

    exit_plan = exit_cmd()
    fun_plan = set_fun_mode(False)
    rhythm_plan = set_rhythm_mode()
    rhythm2_plan = set_rhythm_mode_2()

    for name, p in [("exit", exit_plan), ("fun", fun_plan), ("rhythm", rhythm_plan), ("rhythm2", rhythm2_plan)]:
        for w in p.windows:
            assert w.requires_ack is False, f"{name} requires_ack should be False"
        assert p.ack_policy.ack_per_window is False
        assert p.ack_policy.ack_final is False


# --- Assumption 5: Consistency with sibling simple commands ---

def test_exit_is_raw_no_framing():
    """Exit is a raw byte array (no header/CRC framing) like other simple commands.
    
    Compare with clear/delete/set_power which are all raw byte arrays,
    NOT wrapped in the payloadChannel framing used by image/text.
    """
    from pypixelcolor.commands.clear import clear
    from pypixelcolor.commands.delete import delete
    from pypixelcolor.commands.set_power import set_power

    exit_data = bytes(exit_cmd().windows[0].data)
    clear_data = bytes(clear().windows[0].data)
    power_data = bytes(set_power(True).windows[0].data)
    # All raw commands produce a plain bytes payload in a single window
    assert exit_data == b"\x04\x00\x01\x01"
    assert clear_data == b"\x04\x00\x03\x80"
    assert power_data == b"\x05\x00\x07\x01\x01"
    # No CRC (would be 4 extra bytes), no length-prefix (would be 2 extra bytes)
    assert len(exit_data) == 4


def test_exit_chunk_size_default():
    """Exit uses the default 244-byte chunk size (single small payload)."""
    plan = exit_cmd()
    assert plan.chunk_size == 244


def test_exit_single_window():
    """Exit is a single-window plan (payload < window_size)."""
    plan = exit_cmd()
    windows = list(plan.windows)
    assert len(windows) == 1


# --- Edge cases ---

def test_exit_id_is_exit():
    """The SendPlan id must be 'exit'."""
    assert exit_cmd().id == "exit"


def test_commands_dict_has_exit_entry():
    """COMMANDS['exit'] must map to exit_cmd."""
    assert COMMANDS["exit"] is exit_cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
