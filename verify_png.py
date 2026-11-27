#!/usr/bin/env python3
"""Verify entry.png is a submission-grade PNG.

Checks, in order:
  1. the file is a complete, decodable PNG (Pillow must load every chunk,
     and the image must round-trip through load());
  2. it is exactly 1024x1024;
  3. it is at most 1,048,576 bytes (1 MiB) -- the upload limit;
  4. prints the sha256 so the bundled file can be matched to this run.

Usage:  python verify_png.py [path]      (default: entry.png)
Exit:   0 all checks pass, 1 otherwise.
"""

import hashlib
import os
import sys

from PIL import Image

MAX_BYTES = 1_048_576
SIDE = 1024
MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(msg):
    print(f"FAIL  {msg}")
    return 1


def main(argv):
    path = argv[1] if len(argv) > 1 else "entry.png"

    if not os.path.isfile(path):
        return fail(f"{path}: no such file")

    size = os.path.getsize(path)
    print(f"file   {path}")
    print(f"bytes  {size:,}")

    with open(path, "rb") as fh:
        head = fh.read(8)
    if head != MAGIC:
        return fail(f"not a PNG: header {head!r}")
    print("magic  ok")

    # A truncated file still has the right magic bytes; force a full decode
    # so a half-written chunk or a bad CRC cannot slip through.
    try:
        with Image.open(path) as im:
            im.load()
            w, h = im.size
            mode = im.mode
    except Exception as exc:                       # noqa: BLE001
        return fail(f"PNG will not decode: {exc}")
    print(f"image  {w}x{h} {mode}")

    if (w, h) != (SIDE, SIDE):
        return fail(f"expected {SIDE}x{SIDE}, got {w}x{h}")

    if size > MAX_BYTES:
        return fail(f"{size:,} bytes exceeds the {MAX_BYTES:,}-byte limit "
                    f"by {size - MAX_BYTES:,}")

    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    print(f"sha256 {digest.hexdigest()}")
    print("OK     entry.png is submission-ready")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
