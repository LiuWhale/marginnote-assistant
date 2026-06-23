from __future__ import annotations

import struct
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = ROOT / "extension/codex.mn.assistant/codex.png"


def rgba_pixels(path: Path) -> tuple[int, int, list[tuple[int, int, int, int]]]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AssertionError(f"{path} is not a PNG")
    pos = 8
    width = height = bit_depth = color_type = None
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk_data[:10])
        elif chunk_type == b"IDAT":
            idat.extend(chunk_data)
        elif chunk_type == b"IEND":
            break
    if (bit_depth, color_type) != (8, 6):
        raise AssertionError(f"{path} must be 8-bit RGBA PNG, got bit_depth={bit_depth}, color_type={color_type}")
    assert width is not None and height is not None
    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    rows: list[bytes] = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset : offset + stride])
        offset += stride
        for i, value in enumerate(row):
            left = row[i - 4] if i >= 4 else 0
            up = prev[i]
            up_left = prev[i - 4] if i >= 4 else 0
            if filter_type == 1:
                row[i] = (value + left) & 0xFF
            elif filter_type == 2:
                row[i] = (value + up) & 0xFF
            elif filter_type == 3:
                row[i] = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                p = left + up - up_left
                pa = abs(p - left)
                pb = abs(p - up)
                pc = abs(p - up_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else up_left
                row[i] = (value + predictor) & 0xFF
            elif filter_type != 0:
                raise AssertionError(f"unsupported PNG filter {filter_type}")
        rows.append(bytes(row))
        prev = row
    pixels = []
    for row in rows:
        pixels.extend(struct.iter_unpack("BBBB", row))
    return width, height, list(pixels)


class ToolbarIconAssetTests(unittest.TestCase):
    def test_marginnote_toolbar_icon_is_template_mask_not_filled_square(self) -> None:
        width, height, pixels = rgba_pixels(ICON_PATH)

        self.assertEqual((width, height), (44, 44))
        transparent = sum(1 for *_, alpha in pixels if alpha == 0)
        nontransparent = sum(1 for *_, alpha in pixels if alpha > 0)
        total = len(pixels)
        corner_indices = [0, width - 1, (height - 1) * width, height * width - 1]

        self.assertGreaterEqual(transparent / total, 0.42)
        self.assertLessEqual(nontransparent / total, 0.58)
        for index in corner_indices:
            self.assertEqual(pixels[index][3], 0)


if __name__ == "__main__":
    unittest.main()
