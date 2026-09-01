# -*- coding: utf-8 -*-
"""Interactive TUI tool for previewing and calibrating font rendering on LED matrix screens.

Allows downloading, previewing across 16px/24px/32px matrix heights,
adjusting font_size, offsets, pixel_threshold, var_width mode, and saving permanently to ~/.config/pypixelcolor/fonts.json.
"""

import os
import re
import unicodedata
from logging import getLogger
from pathlib import Path
from typing import Optional

logger = getLogger(__name__)

from PIL import Image, ImageDraw, ImageFont
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Tab,
    Tabs,
)

from ..lib.font_calibrator import (
    calculate_font_metrics,
    delete_cached_metrics,
    download_google_font,
    get_cached_metrics,
    get_fonts_cache_dir,
)
from ..lib.font_config import UNIFONT_PATH
from ..lib.user_config import (
    delete_user_font_metrics,
    get_user_fonts_config_path,
    save_user_font_metrics,
)
from textual import events

WIDGET_HINTS: dict[str, str] = {
    "font-select": "Select active font.",
    "input-test-text": "Preview text on LED matrix (max 16 chars)",
    "tab-16": "Config for screen height 16px",
    "tab-24": "Config for screen height 24px",
    "tab-32": "Config for screen height 32px",
    "input-size": "Font size in pt",
    "input-offx": "Offset X in px",
    "input-offy": "Offset Y in px",
    "input-thresh": "Pixel threshold",
    "btn-var-width": "Hack rendering text as a continuous image then splitting it into regular chunks. Useful for non-monospace font.",
    "btn-auto": "Reset to auto-calibrated values",
    "btn-save": "Save configuration",
    "btn-delete": "Delete this font configuration",
}


class AddFontModal(ModalScreen[Optional[str]]):
    """Modal dialog for downloading or loading a new font."""

    CSS = """
    AddFontModal {
        align: center middle;
    }
    
    #modal-dialog {
        width: 64;
        height: auto;
        border: thick $primary;
        background: $panel;
        padding: 1 2;
    }
    
    #modal-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    #modal-input {
        margin-top: 1;
        margin-bottom: 1;
    }
    
    #modal-buttons {
        height: auto;
        align: right middle;
    }
    
    #modal-buttons Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="modal-dialog"):
            yield Label("Add / Download Font", id="modal-title")
            yield Label("Enter a font family name (e.g. Silkscreen, Press Start 2P)\nor a local file path:")
            yield Input(placeholder="e.g. Silkscreen, Press Start 2P, /path/to/font.ttf", id="modal-input")
            with Horizontal(id="modal-buttons"):
                yield Button("Cancel", id="btn-modal-cancel")
                yield Button("Load", id="btn-modal-load", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-modal-cancel":
            self.dismiss(None)
        elif event.button.id == "btn-modal-load":
            val = self.query_one("#modal-input", Input).value.strip()
            self.dismiss(val if val else None)


class ConfirmDeleteModal(ModalScreen[bool]):
    """Modal dialog to confirm font deletion."""

    CSS = """
    ConfirmDeleteModal {
        align: center middle;
    }
    
    #confirm-dialog {
        width: 52;
        height: auto;
        border: thick $error;
        background: $panel;
        padding: 1 2;
    }
    
    #confirm-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }

    #confirm-message {
        margin-bottom: 1;
    }
    
    #confirm-buttons {
        height: auto;
        align: right middle;
    }
    
    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, font_name: str) -> None:
        super().__init__()
        self.font_name = font_name

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label("Confirm Deletion", id="confirm-title")
            display_name = self.font_name.replace("_", " ")
            yield Label(f"Are you sure you want to delete font '{display_name}'?", id="confirm-message")
            with Horizontal(id="confirm-buttons"):
                yield Button("Cancel", id="btn-confirm-cancel")
                yield Button("Delete", id="btn-confirm-delete", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm-delete":
            self.dismiss(True)
        else:
            self.dismiss(False)



class MatrixPreview(Static):
    """Widget rendering simulated LED matrix pixels for text."""

    def render_matrix(
        self,
        text: str,
        font_path: str,
        height: int,
        font_size: int,
        offset: tuple[int, int],
        pixel_threshold: int,
        var_width: bool = False,
    ) -> Text:
        """Render text onto PIL image and convert to rich Text representing LED pixels.
        
        Args:
            text: Text to render (up to 16 characters).
            font_path: Path to the TTF/OTF font file.
            height: Matrix height in pixels (16, 24, 32).
            font_size: Font size in points.
            offset: (x, y) offset tuple.
            pixel_threshold: Threshold for active pixels (0-255).
            var_width: If True, renders continuously with proportional spacing.
                       If False, renders character by character into fixed cells (8px/16px).
        """
        display_text = text[:16]
        if not display_text or not font_path or not os.path.exists(font_path):
            return Text("No font loaded or empty text.", style="dim italic")

        try:
            font_obj = ImageFont.truetype(font_path, max(1, font_size))
        except Exception as e:
            return Text(f"Font loading error: {e}", style="bold red")

        if var_width:
            # Proportional / continuous chunked rendering
            temp_img = Image.new("L", (2000, height), 0)
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), display_text, font=font_obj)
            rendered_w = max(32, (bbox[2] - bbox[0]) + abs(offset[0]) + 6) if bbox else 32
            max_display_w = rendered_w

            img = Image.new("L", (max_display_w, height), 0)
            draw = ImageDraw.Draw(img)
            draw.text(offset, display_text, fill=255, font=font_obj)
            mode_label = "Variable Width Hack Enabled"
        else:
            # Fixed-width cells mode (standard LED per-character cells)
            is_32 = height >= 32
            half_width = 16 if is_32 else 8
            full_width = 32 if is_32 else 16

            temp_img = Image.new("L", (200, height), 0)
            temp_draw = ImageDraw.Draw(temp_img)

            cell_images = []
            for character in display_text:
                bbox = temp_draw.textbbox((0, 0), character, font=font_obj)
                text_w = (bbox[2] - bbox[0]) if bbox else 0
                is_wide = unicodedata.east_asian_width(character) in ("W", "F") or text_w > int(half_width * 1.25)
                slot_w = full_width if is_wide else half_width

                c_img = Image.new("L", (slot_w, height), 0)
                c_draw = ImageDraw.Draw(c_img)
                c_draw.text(offset, character, fill=255, font=font_obj)
                cell_images.append(c_img)

            total_cell_w = sum(c.width for c in cell_images)
            max_display_w = max(32, total_cell_w)

            img = Image.new("L", (max_display_w, height), 0)
            x_cursor = 0
            for c_img in cell_images:
                img.paste(c_img, (x_cursor, 0))
                x_cursor += c_img.width

            mode_label = f"Fixed Width (cells: {half_width}px / {full_width}px)"

        # Apply threshold to match real hardware binary output (only ON or OFF)
        bin_img = img.point(lambda p: 255 if p >= pixel_threshold else 0, mode="L")
        pbbox = bin_img.getbbox()
        ink_info = f"Ink: {pbbox[2]-pbbox[0]}x{pbbox[3]-pbbox[1]} px" if pbbox else "Ink: 0x0 px"
        bounds_info = f"[Lines {pbbox[1]}..{pbbox[3]-1}]" if pbbox else ""

        result = Text(no_wrap=True)
        result.append(
            f"Matrix {max_display_w} x {height} px  |  {ink_info} {bounds_info}  |  {mode_label}\n",
            style="bold yellow",
        )

        for y in range(height):
            result.append(f"{y:02d}: ", style="dim")
            for x in range(max_display_w):
                if bin_img.getpixel((x, y)) > 0:
                    result.append("██", style="bold cyan")
                else:
                    result.append("··", style="dim")
            result.append("\n")

        return result


class FontTUIApp(App):
    """Textual TUI for font configuration and preview."""

    CSS = """
    Screen {
        background: $surface-darken-1;
    }
    
    #top-bar {
        height: auto;
        padding: 0 1;
        background: $panel;
        border-bottom: solid $primary;
        align: left middle;
    }
    
    #top-bar Horizontal, #top-bar Vertical {
        height: auto;
    }
    
    .top-box {
        height: auto;
        margin-right: 2;
    }
    
    #box-font-select {
        width: 34;
    }
    
    #box-test-text {
        width: 1fr;
    }
    
    #btn-open-add-font {
        margin-top: 1;
        height: 3;
    }
    
    #main-container {
        height: 1fr;
        padding: 1;
    }
    
    #left-panel {
        width: 48;
        height: 100%;
        background: $panel;
        padding: 1;
        border: round $primary;
    }
    
    #right-panel {
        width: 1fr;
        height: 100%;
        margin-left: 1;
        background: $panel;
        padding: 1;
        border: round $primary;
        overflow: auto auto;
    }

    #matrix-preview {
        width: auto;
        height: auto;
    }
    
    .panel-section-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .control-row {
        height: 1;
        margin-bottom: 1;
        align: left middle;
    }
    
    .control-label {
        width: 16;
        content-align: left middle;
    }
    
    .step-btn {
        min-width: 3;
        width: 3;
        height: 1;
        border: none;
        padding: 0;
        margin: 0 1;
    }
    
    .val-input {
        width: 10;
        height: 1;
        border: none;
        padding: 0 1;
        background: $surface;
    }
    
    #btn-var-width {
        min-width: 8;
        width: 8;
        height: 1;
        border: none;
        padding: 0;
        margin-left: 1;
    }
    
    #btn-row {
        margin-top: 1;
        height: 1;
    }
    
    #btn-row Button {
        height: 1;
        border: none;
        padding: 0 1;
        min-width: 10;
        margin-right: 1;
    }
    
    #status-bar {
        width: 100%;
        height: 1;
        background: $surface;
        padding: 0 1;
    }

    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "save_metrics", "Save"),
        ("r", "auto_calibrate", "Reset"),
        ("v", "toggle_var_width", "Toggle Var Width"),
        ("a", "open_add_font", "Add Font"),
        ("d", "delete_font", "Delete Font"),
    ]

    current_font_name = reactive("UNIFONT")
    current_font_path = reactive(UNIFONT_PATH)
    current_height = reactive(16)
    test_text = reactive("Quick fox jumps!")

    # Metrics per height: {16: {...}, 24: {...}, 32: {...}}
    all_metrics: dict[int, dict] = {}
    _blink_timer = None
    _blink_count: int = 0
    _current_status_msg: str = ""
    _current_status_style: str = ""
    _current_hint: str = ""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        preferred_theme = os.getenv("TEXTUAL_THEME", "ansi-dark")
        if preferred_theme in self.available_themes:
            self.theme = preferred_theme
        else:
            self.theme = "ansi-dark"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Horizontal(id="top-bar"):
            with Vertical(classes="top-box", id="box-font-select"):
                yield Label("[b]Font:[/b]")
                yield Select([], id="font-select", prompt="Choose font")
            with Vertical(classes="top-box", id="box-test-text"):
                yield Label(f"[b]Test Text ({len(self.test_text)}/16):[/b]", id="label-test-text")
                yield Input(value=self.test_text, id="input-test-text", max_length=16)

        with Horizontal(id="main-container"):
            with VerticalScroll(id="left-panel"):
                yield Label("Screen Height", classes="panel-section-title")
                yield Tabs(
                    Tab("16 px", id="tab-16"),
                    Tab("24 px", id="tab-24"),
                    Tab("32 px", id="tab-32"),
                    id="height-tabs",
                )

                yield Label("\nCalibration Parameters", classes="panel-section-title")

                with Horizontal(classes="control-row"):
                    yield Label("Font size:", classes="control-label")
                    yield Button("-", id="btn-size-dec", classes="step-btn")
                    yield Input("16", id="input-size", classes="val-input")
                    yield Button("+", id="btn-size-inc", classes="step-btn")

                with Horizontal(classes="control-row"):
                    yield Label("Offset X:", classes="control-label")
                    yield Button("-", id="btn-offx-dec", classes="step-btn")
                    yield Input("0", id="input-offx", classes="val-input")
                    yield Button("+", id="btn-offx-inc", classes="step-btn")

                with Horizontal(classes="control-row"):
                    yield Label("Offset Y:", classes="control-label")
                    yield Button("-", id="btn-offy-dec", classes="step-btn")
                    yield Input("0", id="input-offy", classes="val-input")
                    yield Button("+", id="btn-offy-inc", classes="step-btn")

                with Horizontal(classes="control-row"):
                    yield Label("Threshold:", classes="control-label")
                    yield Button("-", id="btn-thresh-dec", classes="step-btn")
                    yield Input("30", id="input-thresh", classes="val-input")
                    yield Button("+", id="btn-thresh-inc", classes="step-btn")

                with Horizontal(classes="control-row"):
                    yield Label("var_width hack:", classes="control-label")
                    yield Button("OFF", id="btn-var-width", variant="default")

                with Horizontal(id="btn-row"):
                    yield Button("Reset", id="btn-auto", variant="warning")
                    yield Button("Save", id="btn-save", variant="success")
                    yield Button("Delete", id="btn-delete", variant="error")

            with VerticalScroll(id="right-panel"):
                yield MatrixPreview(id="matrix-preview")

        yield Static("", id="status-bar")
        yield Footer()

    PARAMETER_CONTROLS = [
        "input-size",
        "input-offx",
        "input-offy",
        "input-thresh",
        "btn-var-width",
    ]
    ACTION_BUTTONS = [
        "btn-auto",
        "btn-save",
        "btn-delete",
    ]

    def on_mount(self) -> None:
        """Initialize available fonts, disable focus on step buttons, and focus first param."""
        for btn in self.query(".step-btn"):
            btn.can_focus = False
        self._refresh_font_list()
        self._load_current_font_metrics()
        self.query_one("#input-size").focus()

    def on_key(self, event: events.Key) -> None:
        """Enhanced keyboard navigation: arrow keys for parameter navigation & adjustment."""
        focused = self.focused
        f_id = getattr(focused, "id", None)

        # 1. Parameter controls (size, offx, offy, thresh, var_width)
        if f_id in self.PARAMETER_CONTROLS:
            idx = self.PARAMETER_CONTROLS.index(f_id)
            if event.key == "down":
                event.stop()
                event.prevent_default()
                if idx < len(self.PARAMETER_CONTROLS) - 1:
                    self.query_one(f"#{self.PARAMETER_CONTROLS[idx + 1]}").focus()
                else:
                    self.query_one("#btn-save").focus()
                return

            elif event.key == "up":
                event.stop()
                event.prevent_default()
                if idx > 0:
                    self.query_one(f"#{self.PARAMETER_CONTROLS[idx - 1]}").focus()
                else:
                    self.query_one("#height-tabs").focus()
                return

            elif event.key in ("left", "minus", "-"):
                event.stop()
                event.prevent_default()
                if f_id == "input-size":
                    self._adjust_input("#input-size", -1)
                elif f_id == "input-offx":
                    self._adjust_input("#input-offx", -1)
                elif f_id == "input-offy":
                    self._adjust_input("#input-offy", -1)
                elif f_id == "input-thresh":
                    self._adjust_input("#input-thresh", -5)
                elif f_id == "btn-var-width":
                    self.action_toggle_var_width()
                return

            elif event.key in ("right", "plus", "+", "="):
                event.stop()
                event.prevent_default()
                if f_id == "input-size":
                    self._adjust_input("#input-size", 1)
                elif f_id == "input-offx":
                    self._adjust_input("#input-offx", 1)
                elif f_id == "input-offy":
                    self._adjust_input("#input-offy", 1)
                elif f_id == "input-thresh":
                    self._adjust_input("#input-thresh", 5)
                elif f_id == "btn-var-width":
                    self.action_toggle_var_width()
                return

            elif f_id == "btn-var-width" and event.key in ("enter", "space"):
                event.stop()
                event.prevent_default()
                self.action_toggle_var_width()
                return

        # 2. Bottom action buttons (Reset, Save, Delete)
        elif f_id in self.ACTION_BUTTONS:
            idx = self.ACTION_BUTTONS.index(f_id)
            if event.key == "up":
                event.stop()
                event.prevent_default()
                self.query_one("#btn-var-width").focus()
                return
            elif event.key == "down":
                event.stop()
                event.prevent_default()
                self.query_one("#font-select").focus()
                return
            elif event.key == "left" and idx > 0:
                event.stop()
                event.prevent_default()
                self.query_one(f"#{self.ACTION_BUTTONS[idx - 1]}").focus()
                return
            elif event.key == "right" and idx < len(self.ACTION_BUTTONS) - 1:
                event.stop()
                event.prevent_default()
                self.query_one(f"#{self.ACTION_BUTTONS[idx + 1]}").focus()
                return

        # 3. Height tabs
        elif f_id == "height-tabs" or (
            focused and getattr(focused, "parent", None) and getattr(focused.parent, "id", None) == "height-tabs"
        ):
            if event.key == "down":
                event.stop()
                event.prevent_default()
                self.query_one("#input-size").focus()
                return
            elif event.key == "up":
                event.stop()
                event.prevent_default()
                self.query_one("#font-select").focus()
                return

        # 4. Font select widget
        elif f_id == "font-select":
            select_widget = self.query_one("#font-select", Select)
            if not getattr(select_widget, "expanded", False):
                if event.key == "down":
                    event.stop()
                    event.prevent_default()
                    self.query_one("#height-tabs").focus()
                    return
                elif event.key == "right":
                    event.stop()
                    event.prevent_default()
                    self.query_one("#input-test-text").focus()
                    return

        # 5. Test text input
        elif f_id == "input-test-text":
            if event.key == "down":
                event.stop()
                event.prevent_default()
                self.query_one("#height-tabs").focus()
                return
            elif event.key == "up":
                event.stop()
                event.prevent_default()
                self.query_one("#font-select").focus()
                return

        # 6. Global shortcuts when not actively editing text
        if not isinstance(focused, Input):
            if event.key == "1":
                self.query_one("#height-tabs", Tabs).active = "tab-16"
                return
            elif event.key == "2":
                self.query_one("#height-tabs", Tabs).active = "tab-24"
                return
            elif event.key == "3":
                self.query_one("#height-tabs", Tabs).active = "tab-32"
                return

    def _find_widget_hint(self, widget) -> Optional[str]:
        """Find a configured hint for a widget or any of its ancestors."""
        if not widget:
            return None
        for ancestor in getattr(widget, "ancestors_with_self", [widget]):
            if getattr(ancestor, "id", None) in WIDGET_HINTS:
                return WIDGET_HINTS[ancestor.id]
        return None

    def _set_hint(self, hint: str) -> None:
        """Display a helper hint in the status bar if no temporary alert is blinking."""
        self._current_hint = hint
        if self._blink_timer is None:
            try:
                status_bar = self.query_one("#status-bar", Static)
                status_bar.update(f"[cyan]ℹ[/cyan]  {hint}")
            except Exception:
                pass

    def _clear_hint(self) -> None:
        """Clear helper hint from status bar."""
        self._current_hint = ""
        if self._blink_timer is None:
            try:
                status_bar = self.query_one("#status-bar", Static)
                status_bar.update("")
            except Exception:
                pass

    def on_enter(self, event: events.Enter) -> None:
        """Show status bar hint when hovering over an interactive widget."""
        hint = self._find_widget_hint(event.control)
        if hint:
            self._set_hint(hint)

    def on_leave(self, event: events.Leave) -> None:
        """Clear status bar hint when mouse leaves an interactive widget."""
        hint = self._find_widget_hint(event.control)
        if hint and self._current_hint == hint:
            self._clear_hint()

    def on_descendant_focus(self, event: events.DescendantFocus) -> None:
        """Show status bar hint when an interactive widget receives focus."""
        hint = self._find_widget_hint(event.control)
        if hint:
            self._set_hint(hint)

    def on_descendant_blur(self, event: events.DescendantBlur) -> None:
        """Clear status bar hint when an interactive widget loses focus."""
        hint = self._find_widget_hint(event.control)
        if hint and self._current_hint == hint:
            self._clear_hint()

    def _discover_fonts(self) -> list[tuple[str, str, str]]:
        """Discover all available fonts: built-in, cached, and user-configured.
        
        Returns:
            List of (display_label, font_name, font_path).
        """
        fonts: list[tuple[str, str, str]] = []
        if os.path.exists(UNIFONT_PATH):
            fonts.append(("GNU Unifont (built-in)", "UNIFONT", UNIFONT_PATH))

        # Check fonts cache directory
        cache_fonts_dir = get_fonts_cache_dir()
        if cache_fonts_dir.exists():
            for f in sorted(cache_fonts_dir.glob("*.*")):
                if f.suffix.lower() in (".ttf", ".otf"):
                    display_name = f.stem.replace('_', ' ')
                    fonts.append((f"{display_name} (cached)", display_name, str(f)))

        # Also include currently loaded font if not already present
        known_paths = {str(Path(p).resolve()) for _, _, p in fonts}
        if (
            self.current_font_path
            and os.path.exists(self.current_font_path)
            and str(Path(self.current_font_path).resolve()) not in known_paths
        ):
            display_name = self.current_font_name.replace('_', ' ')
            fonts.append((f"{display_name} (local)", self.current_font_name, self.current_font_path))
        elif not any(name.replace('_', ' ').lower() == self.current_font_name.replace('_', ' ').lower() for _, name, _ in fonts):
            fonts.append((f"{self.current_font_name} (loaded)", self.current_font_name, self.current_font_path))

        return fonts

    def _refresh_font_list(self) -> None:
        """Update the font select widget."""
        discovered = self._discover_fonts()
        options = [(label, name) for label, name, _ in discovered]
        select_widget = self.query_one("#font-select", Select)
        select_widget.set_options(options)
        valid_values = [name for _, name in options]

        matching_val = None
        for val in valid_values:
            if val == self.current_font_name or val.replace('_', ' ').lower() == self.current_font_name.replace('_', ' ').lower():
                matching_val = val
                break

        if matching_val:
            self.current_font_name = matching_val
            select_widget.value = matching_val
        elif valid_values:
            self.current_font_name = valid_values[0]
            select_widget.value = valid_values[0]

    def _load_current_font_metrics(self) -> None:
        """Load or calculate metrics for current font across all heights."""
        self.all_metrics = get_cached_metrics(
            self.current_font_path,
            heights=(16, 24, 32),
            font_name=self.current_font_name,
        )
        self._sync_inputs_from_metrics()
        self._update_preview()

    def _sync_inputs_from_metrics(self) -> None:
        """Update control input fields with current height's metrics."""
        m = self.all_metrics.get(
            self.current_height,
            {"font_size": self.current_height, "offset": (0, 0), "pixel_threshold": 30, "var_width": False},
        )
        self.query_one("#input-size", Input).value = str(m["font_size"])
        self.query_one("#input-offx", Input).value = str(m["offset"][0])
        self.query_one("#input-offy", Input).value = str(m["offset"][1])
        self.query_one("#input-thresh", Input).value = str(m["pixel_threshold"])

        var_w = bool(m.get("var_width", False))
        btn_var = self.query_one("#btn-var-width", Button)
        btn_var.label = "ON" if var_w else "OFF"
        btn_var.variant = "success" if var_w else "default"

    def _update_preview(self) -> None:
        """Refresh the matrix preview widget with current parameters."""
        m = self.all_metrics.get(
            self.current_height,
            {"font_size": self.current_height, "offset": (0, 0), "pixel_threshold": 30, "var_width": False},
        )
        preview = self.query_one("#matrix-preview", MatrixPreview)
        rendered = preview.render_matrix(
            text=self.test_text,
            font_path=self.current_font_path,
            height=self.current_height,
            font_size=m["font_size"],
            offset=m["offset"],
            pixel_threshold=m["pixel_threshold"],
            var_width=bool(m.get("var_width", False)),
        )
        preview.update(rendered)

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle font selection change."""
        if not event.value or event.value == Select.BLANK:
            return
        selected_name = str(event.value)
        if selected_name == self.current_font_name:
            return
        for _, name, path in self._discover_fonts():
            if name == selected_name:
                self.current_font_name = name
                self.current_font_path = path
                self._load_current_font_metrics()
                break

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle real-time changes in inputs."""
        if event.input.id == "input-test-text":
            if len(event.value) > 16:
                event.input.value = event.value[:16]
                return
            self.test_text = event.value
            lbl = self.query_one("#label-test-text", Label)
            lbl.update(f"[b]Test Text ({len(self.test_text)}/16):[/b]")
            self._update_preview()
        elif event.input.id in ("input-size", "input-offx", "input-offy", "input-thresh"):
            self._update_metrics_from_inputs()

    def _update_metrics_from_inputs(self) -> None:
        """Read values from inputs and update current height metrics."""
        try:
            sz = int(self.query_one("#input-size", Input).value)
            off_x = int(self.query_one("#input-offx", Input).value)
            off_y = int(self.query_one("#input-offy", Input).value)
            thresh = int(self.query_one("#input-thresh", Input).value)
        except ValueError:
            return

        current_var = self.all_metrics.get(self.current_height, {}).get("var_width", False)
        self.all_metrics[self.current_height] = {
            "font_size": max(1, sz),
            "offset": (off_x, off_y),
            "pixel_threshold": max(0, min(255, thresh)),
            "var_width": current_var,
        }
        self._update_preview()

    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle height tab switch (16, 24, 32)."""
        tab_id = event.tab.id
        if tab_id == "tab-16":
            self.current_height = 16
        elif tab_id == "tab-24":
            self.current_height = 24
        elif tab_id == "tab-32":
            self.current_height = 32

        self._sync_inputs_from_metrics()
        self._update_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        btn_id = event.button.id
        if btn_id == "btn-open-add-font":
            self.action_open_add_font()
        elif btn_id == "btn-size-inc":
            self._adjust_input("#input-size", 1)
        elif btn_id == "btn-size-dec":
            self._adjust_input("#input-size", -1)
        elif btn_id == "btn-offx-inc":
            self._adjust_input("#input-offx", 1)
        elif btn_id == "btn-offx-dec":
            self._adjust_input("#input-offx", -1)
        elif btn_id == "btn-offy-inc":
            self._adjust_input("#input-offy", 1)
        elif btn_id == "btn-offy-dec":
            self._adjust_input("#input-offy", -1)
        elif btn_id == "btn-thresh-inc":
            self._adjust_input("#input-thresh", 5)
        elif btn_id == "btn-thresh-dec":
            self._adjust_input("#input-thresh", -5)
        elif btn_id == "btn-var-width":
            self.action_toggle_var_width()
        elif btn_id == "btn-auto":
            self.action_auto_calibrate()
        elif btn_id == "btn-save":
            self.action_save_metrics()
        elif btn_id == "btn-delete":
            self.action_delete_font()

    def action_open_add_font(self) -> None:
        """Open the Add Font modal dialog."""
        def _on_modal_dismiss(font_query: Optional[str]) -> None:
            if font_query:
                self._load_or_download_font(font_query)

        self.push_screen(AddFontModal(), _on_modal_dismiss)

    def action_toggle_var_width(self) -> None:
        """Toggle variable width mode for current height."""
        current = bool(self.all_metrics.get(self.current_height, {}).get("var_width", False))
        new_val = not current
        if self.current_height in self.all_metrics:
            self.all_metrics[self.current_height]["var_width"] = new_val

        btn_var = self.query_one("#btn-var-width", Button)
        btn_var.label = "ON" if new_val else "OFF"
        btn_var.variant = "success" if new_val else "default"
        self._update_preview()
        self._set_status(f"Variable width set to {'ON' if new_val else 'OFF'} for {self.current_height}px.")

    def _adjust_input(self, selector: str, delta: int) -> None:
        """Helper to increment/decrement integer value in an Input widget."""
        inp = self.query_one(selector, Input)
        try:
            val = int(inp.value) + delta
        except ValueError:
            val = delta
        inp.value = str(val)
        self._update_metrics_from_inputs()

    def _load_or_download_font(self, font_query: str) -> None:
        """Download font or load local path."""
        raw_val = font_query.strip()
        if not raw_val:
            return

        self._set_status(f"Loading '{raw_val}'...")

        try:
            if os.path.exists(raw_val):
                path = str(Path(raw_val).resolve())
                name = Path(path).stem
            else:
                # Treat as downloadable font family
                path = str(download_google_font(raw_val))
                name = raw_val

            self.current_font_name = name
            self.current_font_path = path
            self._refresh_font_list()
            self._load_current_font_metrics()
            display_name = name.replace("_", " ")
            self._set_status(f"Font '{display_name}' loaded successfully.")
        except Exception as e:
            self._set_status(f"Failed to load font: {e}", error=True)

    def action_auto_calibrate(self) -> None:
        """Reset current height metrics to auto-calibrated values."""
        calibrated = calculate_font_metrics(self.current_font_path, self.current_height)
        self.all_metrics[self.current_height] = calibrated
        self._sync_inputs_from_metrics()
        self._update_preview()
        self._set_status(f"Reset applied for {self.current_height}px.")

    def action_save_metrics(self) -> None:
        """Save permanent configuration to ~/.config/pypixelcolor/fonts.json."""
        try:
            save_user_font_metrics(
                font_path=self.current_font_path,
                font_name=self.current_font_name,
                metrics=self.all_metrics,
            )
            config_file = get_user_fonts_config_path()
            self._set_status(f"Configuration saved to {config_file}.")
        except Exception as e:
            self._set_status(f"Failed to save: {e}", error=True)

    def action_delete_font(self) -> None:
        """Delete the font currently being configured (except built-in)."""
        font_name = self.current_font_name
        font_path = Path(self.current_font_path).resolve()
        unifont_resolved = Path(UNIFONT_PATH).resolve()

        if font_name.upper() == "UNIFONT" or font_path == unifont_resolved:
            self._set_status("Cannot delete built-in font UNIFONT.", error=True)
            return

        def _on_modal_dismiss(confirmed: Optional[bool]) -> None:
            if confirmed:
                self._perform_delete_font(font_name, font_path)

        self.push_screen(ConfirmDeleteModal(font_name), _on_modal_dismiss)

    def _perform_delete_font(self, font_name: str, font_path: Path) -> None:
        """Perform font deletion after user confirmation."""
        unifont_resolved = Path(UNIFONT_PATH).resolve()
        try:
            # 1. Remove from user permanent configuration (~/.config/pypixelcolor/fonts.json)
            delete_user_font_metrics(str(font_path), font_name)

            # 2. Remove from cache font metrics (~/.cache/pypixelcolor/font_metrics.json)
            delete_cached_metrics(str(font_path), font_name)

            # 3. Delete font file from disk if it exists and is not UNIFONT
            if font_path.exists() and font_path != unifont_resolved:
                try:
                    font_path.unlink()
                except Exception as e:
                    logger.warning("Could not delete font file %s: %s", font_path, e)

            # Also check cache directory for any cached copies with matching safe name
            fonts_dir = get_fonts_cache_dir()
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', font_name)
            for ext in (".ttf", ".otf"):
                cached_candidate = fonts_dir / f"{safe_name}{ext}"
                if cached_candidate.exists() and cached_candidate.resolve() != unifont_resolved:
                    try:
                        cached_candidate.unlink()
                    except Exception:
                        pass

            # 4. Reset selection back to UNIFONT
            self.current_font_name = "UNIFONT"
            self.current_font_path = UNIFONT_PATH
            self._refresh_font_list()
            self._load_current_font_metrics()
            display_name = font_name.replace("_", " ")
            self._set_status(f"Font '{display_name}' deleted.")
        except Exception as e:
            self._set_status(f"Failed to delete font: {e}", error=True)


    def _set_status(self, msg: str, error: bool = False) -> None:
        """Display feedback in the bottom full-width status bar, blinking for 2 seconds."""
        status_bar = self.query_one("#status-bar", Static)
        if not msg:
            status_bar.update("")
            return

        if self._blink_timer is not None:
            self._blink_timer.stop()
            self._blink_timer = None

        color = "bold red" if error else "bold green"
        self._current_status_msg = msg
        self._current_status_style = color
        self._blink_count = 0

        def _blink_step() -> None:
            self._blink_count += 1
            if self._blink_count >= 8:
                if self._blink_timer is not None:
                    self._blink_timer.stop()
                    self._blink_timer = None
                if self._current_hint:
                    status_bar.update(f"[cyan]ℹ[/cyan]  {self._current_hint}")
                else:
                    status_bar.update(f"[{self._current_status_style}] {self._current_status_msg}[/{self._current_status_style}]")
            elif self._blink_count % 2 == 1:
                status_bar.update("")
            else:
                status_bar.update(f"[{self._current_status_style}] {self._current_status_msg}[/{self._current_status_style}]")

        status_bar.update(f"[{color}] {msg}[/{color}]")
        self._blink_timer = self.set_interval(0.25, _blink_step)


def run_font_tui() -> None:
    """Launch the Font Configuration TUI."""
    app = FontTUIApp()
    app.run()


if __name__ == "__main__":
    run_font_tui()
