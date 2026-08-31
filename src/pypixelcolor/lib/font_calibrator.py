# -*- coding: utf-8 -*-
"""Font metric calibration and persistent disk cache."""

import os
import json
import hashlib
import urllib.request
import urllib.parse
import re
from logging import getLogger
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

logger = getLogger(__name__)

def get_cache_dir() -> Path:
    """Return the user cache directory for pypixelcolor, creating it if needed."""
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        cache_dir = Path(xdg_cache) / "pypixelcolor"
    else:
        cache_dir = Path.home() / ".cache" / "pypixelcolor"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _compute_otsu_threshold(img: Image.Image) -> int:
    """Compute optimal binarization threshold using Otsu's method."""
    hist = img.histogram()
    total_pixels = sum(hist)
    if total_pixels == 0:
        return 70

    current_max = 0.0
    threshold = 70
    sum_total = sum(i * hist[i] for i in range(256))
    sum_b = 0.0
    w_b = 0

    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total_pixels - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        between_var = w_b * w_f * ((m_b - m_f) ** 2)
        if between_var > current_max:
            current_max = between_var
            threshold = t

    return max(30, min(180, threshold))


def calculate_font_metrics(font_path: str, target_height: int) -> dict:
    """Calculate rendering metrics (font_size, offset, pixel_threshold) for a font at target_height.
    
    Args:
        font_path: Absolute or relative path to TTF/OTF font file.
        target_height: Target character matrix height (e.g. 16, 24, 32).
        
    Returns:
        Dictionary with font_size (int), offset (tuple[int, int]), pixel_threshold (int).
    """
    try:
        f_test = ImageFont.truetype(font_path, target_height)
    except Exception as e:
        raise ValueError(f"Failed to load font '{font_path}': {e}")

    # Determine reference sample:
    # If font supports CJK, include CJK reference character '国'
    has_cjk = False
    try:
        bb_cjk = f_test.getbbox("国")
        if bb_cjk and (bb_cjk[2] - bb_cjk[0]) > 0:
            has_cjk = True
    except Exception:
        has_cjk = False

    sample_text = "HAM08Éêgqpyjç国" if has_cjk else "HAM08Éêgqpyjç"

    # 1. Search for optimal font_size where actual rendered ink <= target_height
    min_sz = max(6, int(target_height * 0.4))
    max_sz = int(target_height * 2.5)

    best_size = min_sz
    canvas_h = target_height * 3
    draw_y = target_height

    for sz in range(min_sz, max_sz + 1):
        f = ImageFont.truetype(font_path, sz)
        canvas = Image.new("L", (500, canvas_h), 0)
        d = ImageDraw.Draw(canvas)
        d.text((0, draw_y), sample_text, fill=255, font=f)
        pbbox = canvas.getbbox()
        if pbbox:
            ink_h = pbbox[3] - pbbox[1]
            if ink_h <= target_height:
                best_size = sz
            else:
                break

    font_obj = ImageFont.truetype(font_path, best_size)

    # 2. Auto-centering offset based on the exact same full-span reference
    canvas = Image.new("L", (500, canvas_h), 0)
    d = ImageDraw.Draw(canvas)
    d.text((0, draw_y), sample_text, fill=255, font=font_obj)
    pbbox = canvas.getbbox()
    if pbbox:
        ink_top = pbbox[1] - draw_y
        ink_bottom = pbbox[3] - draw_y
        actual_ink_h = ink_bottom - ink_top
        y_offset = (target_height - actual_ink_h) // 2 - ink_top
    else:
        y_offset = 0

    # 3. Otsu thresholding for optimal contrast
    render_sample = "ABCDEFabcdef0123456789你好世界" if has_cjk else "ABCDEFabcdef0123456789"
    img_sample = Image.new("L", (400, target_height * 2), 0)
    draw_sample = ImageDraw.Draw(img_sample)
    draw_sample.text((0, 0), render_sample, fill=255, font=font_obj)
    pixel_threshold = _compute_otsu_threshold(img_sample)

    return {
        "font_size": best_size,
        "offset": (0, y_offset),
        "pixel_threshold": pixel_threshold,
    }


def _get_font_cache_key(font_path: str, font_name: Optional[str] = None) -> str:
    """Generate a readable unique cache key based on font name, file path, size, and modification time."""
    p = Path(font_path).resolve()
    stat = p.stat()
    raw = f"{p.name}_{stat.st_size}_{stat.st_mtime_ns}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    name_prefix = re.sub(r'[^a-zA-Z0-9_-]', '_', font_name or p.stem)
    return f"{name_prefix}_{h}"


def get_cached_metrics(font_path: str, heights: tuple[int, ...] = (16, 24, 32), font_name: Optional[str] = None) -> dict[int, dict]:
    """Retrieve or compute font metrics for requested heights, persisting them in disk cache.
    
    Args:
        font_path: Path to font file.
        heights: Heights to retrieve or calibrate (default 16, 24, 32).
        font_name: Optional human-readable font name for identification in the cache.
        
    Returns:
        Dict mapping height (int) to metrics dict {font_size, offset, pixel_threshold}.
    """
    cache_file = get_cache_dir() / "font_metrics.json"
    cache_data = {}

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        except Exception:
            cache_data = {}

    resolved_name = font_name or Path(font_path).stem
    cache_key = _get_font_cache_key(font_path, resolved_name)
    font_entry = cache_data.get(cache_key)
    if font_entry is None:
        p = Path(font_path).resolve()
        stat = p.stat()
        old_h = hashlib.sha256(f"{p.name}_{stat.st_size}_{stat.st_mtime_ns}".encode("utf-8")).hexdigest()[:16]
        font_entry = cache_data.get(old_h, {})

    dirty = False
    if "name" in font_entry:
        del font_entry["name"]
        dirty = True
    if "file" in font_entry:
        del font_entry["file"]
        dirty = True

    result = {}
    for h in heights:
        h_str = str(h)
        if h_str in font_entry:
            entry = font_entry[h_str]
            result[h] = {
                "font_size": entry["font_size"],
                "offset": tuple(entry["offset"]),
                "pixel_threshold": entry["pixel_threshold"],
            }
        else:
            computed = calculate_font_metrics(font_path, h)
            font_entry[h_str] = {
                "font_size": computed["font_size"],
                "offset": list(computed["offset"]),
                "pixel_threshold": computed["pixel_threshold"],
            }
            result[h] = computed
            dirty = True

    if dirty:
        cache_data[cache_key] = font_entry
        try:
            temp_file = cache_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            temp_file.replace(cache_file)
        except Exception:
            pass  # Non-fatal if writing to cache fails

    return result


def get_fonts_cache_dir() -> Path:
    """Return the user fonts cache directory (~/.cache/pypixelcolor/fonts)."""
    fonts_dir = get_cache_dir() / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    return fonts_dir


def download_google_font(family: str, timeout: int = 15) -> Path:
    """Download a Google Font TTF file by family name into local cache.
    
    Args:
        family: Google Font family name (e.g. 'Silkscreen', 'Press Start 2P').
        timeout: HTTP request timeout in seconds.
        
    Returns:
        Path to cached .ttf file.
        
    Raises:
        ValueError: If font cannot be found on Google Fonts.
    """
    family = family.strip()
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', family)
    fonts_dir = get_fonts_cache_dir()
    target_path = fonts_dir / f"{safe_name}.ttf"

    if target_path.exists() and target_path.stat().st_size > 0:
        return target_path

    url_name = urllib.parse.quote_plus(family)
    css_url = f"https://fonts.googleapis.com/css2?family={url_name}"
    req = urllib.request.Request(css_url, headers={"User-Agent": "curl/7.68.0"})

    try:
        logger.info("Downloading font at : " + css_url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            css = resp.read().decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to query Google Fonts for '{family}': {e}")

    match = re.search(r"url\((https://[^\)]+\.ttf)\)", css)
    if not match:
        match = re.search(r"url\((https://[^\)]+)\)", css)
    if not match:
        raise ValueError(f"Could not resolve download URL for Google Font '{family}'")

    ttf_url = match.group(1)
    tmp_path = target_path.with_suffix(".tmp")
    try:
        urllib.request.urlretrieve(ttf_url, tmp_path)
        tmp_path.replace(target_path)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise ValueError(f"Failed to download Google Font '{family}' from {ttf_url}: {e}")

    logger.info("Download completed.")

    return target_path


def download_font_url(url: str, timeout: int = 15) -> Path:
    """Download a font from a direct HTTP/HTTPS URL into local cache.
    
    Args:
        url: Direct URL to font file.
        timeout: HTTP request timeout in seconds.
        
    Returns:
        Path to cached font file.
    """
    url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    ext = Path(urllib.parse.urlparse(url).path).suffix or ".ttf"
    target_path = get_fonts_cache_dir() / f"font_{url_hash}{ext}"

    if target_path.exists() and target_path.stat().st_size > 0:
        return target_path

    tmp_path = target_path.with_suffix(".tmp")
    req = urllib.request.Request(url, headers={"User-Agent": "pypixelcolor/0.5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp_path, "wb") as out:
            out.write(resp.read())
        tmp_path.replace(target_path)
    except Exception as e:
        if tmp_path.exists():
            tmp_path.unlink()
        raise ValueError(f"Failed to download font from '{url}': {e}")

    return target_path

