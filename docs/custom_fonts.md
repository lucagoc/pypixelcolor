# Custom Fonts

The library comes with built-in support for several fonts (CUSONG, SIMSUN, VCR_OSD_MONO). However, you can also use your own TTF files.

## Usage

To use a custom font with the pypixelcolor library, you can specify the path to your TTF font file when sending text. Below is an example of how to do this:

```python
import pypixelcolor

if __name__ == "__main__":
    client = pypixelcolor.Client("AF:1D:E1:BD:5C:80")
    client.connect()
    client.send_text("Hello", font="./Minecraft.ttf")
    client.disconnect()
```

A file must be created named with the same name as the TTF file but with a `.json` extension (e.g., `Minecraft.json`) in the same directory as the TTF file, containing the font metadata. Here is an example of what the JSON file should look like:

```json
{
  "name": "Minecraft",
  "metrics": {
    "16": {
      "font_size": 16,
      "offset": [0, 0],
      "pixel_threshold": 70
    },
    "20": {
      "font_size": 20,
      "offset": [0, 0],
      "pixel_threshold": 70
    },
    "24": {
      "font_size": 24,
      "offset": [0, -1],
      "pixel_threshold": 80
    },
    "32": {
      "font_size": 25,
      "offset": [0, 2],
      "pixel_threshold": 85
    }
  }
}
```

### JSON File Structure

- `name`: The name of the font.
- `metrics`: A dictionary where each key is a character height size (in pixels, 16, 20, 24 or 32) and the value is another dictionary containing:
  - `font_size`: The size of the font to be used.
  - `offset`: A list of two integers representing the x and y offset for rendering the font.
  - `pixel_threshold`: An integer value that determines the pixel intensity threshold for rendering the font.

## Notes

- Ensure that the TTF and JSON files are in the same directory.
- The font sizes specified in the JSON file should match the sizes you intend to use when sending text.
- Adjust the `offset` and `pixel_threshold` values as needed to achieve the desired appearance on your pixel device.
