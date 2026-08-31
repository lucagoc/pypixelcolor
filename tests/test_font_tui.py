# -*- coding: utf-8 -*-
"""Tests for Font Configuration TUI."""

import pytest
from textual.widgets import Input
from pypixelcolor.tools.font_tui import FontTUIApp, MatrixPreview
from pypixelcolor.lib.font_config import UNIFONT_PATH
from pypixelcolor.lib.user_config import get_user_font_metrics


def test_font_tui_app_lifecycle(tmp_path, monkeypatch):
    """Test full TUI app lifecycle: tabs, controls, auto-calibration, and saving."""
    import asyncio
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    async def _run():
        app = FontTUIApp()
        async with app.run_test(size=(160, 50)) as pilot:
            # 1. Verify initial state
            assert app.current_font_name == "UNIFONT"
            assert app.current_height == 16
            assert 16 in app.all_metrics

            # 2. Test tab switching
            tabs = app.query_one("#height-tabs")
            tabs.active = "tab-24"
            await pilot.pause()
            assert app.current_height == 24

            # 3. Test metric adjustment buttons
            old_size = app.all_metrics[24]["font_size"]
            app.query_one("#btn-size-inc").press()
            await pilot.pause()
            assert app.all_metrics[24]["font_size"] == old_size + 1

            app.query_one("#btn-offy-dec").press()
            await pilot.pause()
            assert app.all_metrics[24]["offset"][1] == -1

            # 4. Test var_width toggle button (24px defaults to ON for UNIFONT)
            btn_var = app.query_one("#btn-var-width")
            assert str(btn_var.label) == "ON"
            btn_var.press()
            await pilot.pause()
            assert app.all_metrics[24]["var_width"] is False
            assert str(btn_var.label) == "OFF"
            btn_var.press()
            await pilot.pause()
            assert app.all_metrics[24]["var_width"] is True
            assert str(btn_var.label) == "ON"

            # 5. Test saving configuration
            app.action_save_metrics()
            await pilot.pause()

            # Check saved user config
            saved = get_user_font_metrics(UNIFONT_PATH, "UNIFONT")
            assert saved is not None
            assert 24 in saved
            assert saved[24]["var_width"] is True

            # 6. Test auto-calibration
            app.action_auto_calibrate()
            await pilot.pause()
            assert 24 in app.all_metrics

            # 7. Test matrix preview rendering (English output)
            preview = app.query_one("#matrix-preview", MatrixPreview)
            rendered = preview.render_matrix(
                text="TEST",
                font_path=UNIFONT_PATH,
                height=16,
                font_size=16,
                offset=(0, 0),
                pixel_threshold=30,
                var_width=True,
            )
            assert "Matrix" in rendered.plain
            assert "16 px" in rendered.plain
            assert "Variable Width" in rendered.plain

            # Exit app
            await pilot.press("q")

    asyncio.run(_run())


def test_font_tui_download_font(tmp_path, monkeypatch):
    """Test loading/downloading a font in TUI."""
    import asyncio
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    # Mock download_google_font to return UNIFONT_PATH
    monkeypatch.setattr(
        "pypixelcolor.tools.font_tui.download_google_font",
        lambda family: UNIFONT_PATH,
    )

    async def _run():
        app = FontTUIApp()
        async with app.run_test(size=(160, 50)) as pilot:
            app.action_open_add_font()
            await pilot.pause()

            modal_inp = app.screen.query_one("#modal-input", Input)
            modal_inp.value = "Silkscreen"
            app.screen.query_one("#btn-modal-load").press()
            await pilot.pause()

            assert app.current_font_name == "Silkscreen"
            await pilot.press("q")

    asyncio.run(_run())
