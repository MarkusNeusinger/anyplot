"""PNG hardening (gate R2) and the canvas padding fallback of gate R3.

A render's PNG is untrusted: the code that wrote it came from a model. Before any
byte of it reaches a reviewer, a store or a browser, `read_output` reads it from the
run directory without following links and under a size cap, and `harden` checks the
signature, decodes it with Pillow under a pixel cap, refuses a blank canvas, and
re-encodes it, which drops every ancillary chunk (text, EXIF, ICC) the code may have
written. Only the re-encoded bytes travel on.

`pad_to` is the R3 fallback when the canvas is still off target after the single
repair: it pads the image onto the target canvas with its own background colour and
never crops. An image larger than the target is first scaled down to fit, keeping its
aspect ratio, because cropping would cut data or labels.
"""

import io
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from core.canvas import PNG_SIGNATURE, dominant_color


MAX_PNG_BYTES = 10 * 1024 * 1024
MAX_PROBE_BYTES = 256 * 1024
MAX_IMAGE_PIXELS = 3200 * 1800 * 2  # twice the canvas leaves room for a drifted size, not for a bomb
# R2 fails only a canvas that is 98 % one colour. The rubric's AR-04 uses 95 %, which
# sparse dark renders reach legitimately (core/canvas.py), so R2 stays more permissive.
MAX_BACKGROUND_RATIO = 0.98


class PngRejected(ValueError):
    """The output is not a PNG the host accepts; the message is safe to show to the adapter."""


@dataclass(frozen=True)
class HardenedPng:
    """A re-encoded PNG and its size."""

    data: bytes
    width: int
    height: int


def read_output(path: Path, max_bytes: int) -> bytes | None:
    """The bytes of a regular file the run left, or None when it is missing.

    Refuses symlinks and anything that is not a regular file (`lstat`, then
    `O_NOFOLLOW`), and files above `max_bytes`, so a render cannot make the host
    read outside its run directory or exhaust memory.
    """
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise PngRejected(f"{path.name} is not a regular file")
    if info.st_size > max_bytes:
        raise PngRejected(f"{path.name} is {info.st_size} bytes, more than the {max_bytes}-byte limit")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise PngRejected(f"{path.name} grew past the {max_bytes}-byte limit while it was read")
    return data


def harden(data: bytes) -> HardenedPng:
    """R2: signature, decode under the pixel cap, not blank, re-encoded."""
    if len(data) > MAX_PNG_BYTES:
        raise PngRejected(f"the PNG is {len(data)} bytes, more than the {MAX_PNG_BYTES}-byte limit")
    if not data.startswith(PNG_SIGNATURE):
        raise PngRejected("the output does not start with the PNG signature")
    previous = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG":
                raise PngRejected("the output is not a PNG image")
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                raise PngRejected(f"the image is {width}x{height}, more pixels than allowed")
            image.load()
            rgb = image.convert("RGB")
    except PngRejected:
        raise
    except (Image.DecompressionBombError, OSError, ValueError) as exc:
        raise PngRejected(f"the PNG does not decode ({type(exc).__name__})") from None
    finally:
        Image.MAX_IMAGE_PIXELS = previous
    (red, green, blue), ratio = dominant_color(rgb)
    if ratio >= MAX_BACKGROUND_RATIO:
        raise PngRejected(
            f"the image is {ratio * 100:.0f}% one colour (#{red:02X}{green:02X}{blue:02X}); nothing was drawn"
        )
    buffer = io.BytesIO()
    rgb.save(buffer, format="PNG", optimize=False)
    return HardenedPng(buffer.getvalue(), width, height)


def size_of(data: bytes) -> tuple[int, int]:
    """The pixel size of a PNG the host already hardened."""
    with Image.open(io.BytesIO(data)) as image:
        width, height = image.size
    return width, height


def pad_to(data: bytes, target: tuple[int, int]) -> bytes:
    """The image centred on a `target` canvas of its own background colour; never cropped."""
    with Image.open(io.BytesIO(data)) as source:
        image = source.convert("RGB")
    background, _ = dominant_color(image)
    width, height = image.size
    target_width, target_height = target
    if width > target_width or height > target_height:
        scale = min(target_width / width, target_height / height)
        image = image.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.LANCZOS)
        width, height = image.size
    canvas = Image.new("RGB", target, background)
    canvas.paste(image, ((target_width - width) // 2, (target_height - height) // 2))
    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    return buffer.getvalue()
