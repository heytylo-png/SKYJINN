#!/usr/bin/env python3
"""Re-embed art/maps/v2/*.png into MAP_SRC data URIs in index.html as WebP.

Run from the repo root:  python3 tools/embed_maps.py
Does not bump sw.js; do that by hand after a visual check.
"""
from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# Keys in MAP_SRC. "dunes" in game code maps to "desert".
MAP_KEYS = ("desert", "bridge", "volcano", "frost", "jungle")
QUALITY = 85
METHOD = 6


def encode_webp(path: Path) -> tuple[bytes, tuple[int, int]]:
    im = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=QUALITY, method=METHOD)
    return buf.getvalue(), im.size


def main() -> int:
    html_path = ROOT / "index.html"
    html = html_path.read_text()
    m = re.search(r"const MAP_SRC=\{.*?\};", html, re.S)
    if not m:
        print("MAP_SRC block not found", file=sys.stderr)
        return 1
    entries = []
    for key in MAP_KEYS:
        png = ROOT / "art" / "maps" / "v2" / f"{key}.png"
        if not png.exists():
            print("missing", png, file=sys.stderr)
            return 1
        data, size = encode_webp(png)
        b64 = base64.b64encode(data).decode("ascii")
        uri = f"data:image/webp;base64,{b64}"
        entries.append(f'"{key}": "{uri}"')
        print(f"{key}: {size[0]}x{size[1]}  webp {len(data)} bytes  from {png.stat().st_size}")
    block = "const MAP_SRC={" + ", ".join(entries) + "};"
    html2 = html[: m.start()] + block + html[m.end() :]
    html_path.write_text(html2)
    print("updated", html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
