# Sending Content

## `send_image`

![Send Image](../assets/gifs/send_image.gif)

::: pypixelcolor.commands.send_image.send_image
    options:
      show_root_heading: false
      show_root_toc_entry: false

## `send_image_hex`

::: pypixelcolor.commands.send_image.send_image_hex
    options:
      show_root_heading: false
      show_root_toc_entry: false

## `send_text`

![Send Text](../assets/gifs/send_text.gif)

::: pypixelcolor.commands.send_text.send_text
    options:
      show_root_heading: false
      show_root_toc_entry: false

### Inline Color Tags

`send_text` supports inline hex color tags to style individual words or characters:

- Opening tag: `[#RRGGBB]` or `[RRGGBB]`
- Closing tag: `[/]`, `[/#]`, or `[/color]`

```python
# Multi-colored text
client.send_text("[#ff0000]Red[/] [#00ff00]Green[/] [#0000ff]Blue[/]")

# Nested tags (closes back to the parent color)
client.send_text("[#ffaa00]Orange [#ffffff]White[/] Orange[/]")
```

```bash
pypixelcolor -a <MAC_ADDRESS> -c send_text "[#ff0000]Red[/] [#00ff00]Green[/] [#0000ff]Blue[/]"
```

!!! note
    Inline color tags are supported with standard font rendering. When variable-width mode is enabled (`var_width=True`), color tags are ignored with a warning and the uniform `color` parameter is used instead.

### Font Selection

The `font` argument supports multiple formats:

- **Built-in Font**: `"UNIFONT"` (default GNU Unifont with comprehensive Unicode and CJK glyph support).
- **Google Fonts**: Specify any [Google Font](https://fonts.google.com/) name directly (e.g. `font="Silkscreen"`, `font="Press Start 2P"`). It will be downloaded automatically and calibrated on first run.
- **Local Font**: Provide a relative or absolute path to a `.ttf` or `.otf` file (e.g. `font="./Minecraft.ttf"`).
- **FontConfig**: Pass a pre-configured `FontConfig` object.

You can also calibrate and adjust fonts interactively using `pypixelcolor --font-config`.
