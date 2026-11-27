#!/usr/bin/env python3
"""Deploy the bundled entry.png into the output directory, atomically.

The grading harness runs this from an arbitrary working directory and reads
$MAKEFUN_OUTPUT_DIR (default /output). The bundled artwork sits next to this
file, so the source path is resolved from __file__, never from cwd.

Deploy is staged and atomic:
  1. read the bundled entry.png and validate it (PNG magic, IHDR size,
     byte budget) before touching the output directory;
  2. mkstemp a staging file *inside* the output directory, so the final
     rename is same-filesystem and therefore atomic;
  3. write, fsync, chmod 0644 (mkstemp creates 0600), close;
  4. re-validate the staged bytes, then os.replace() onto the destination;
  5. re-validate the destination from disk.

Standard library only. Exits non-zero with a clear message on any failure,
leaving no partial file behind.
"""

import os
import struct
import sys
import tempfile

MAX_BYTES = 1_048_576
SIDE = 1024
MAGIC = b"\x89PNG\r\n\x1a\n"
IHDR = b"IHDR"
NAME = "entry.png"


class DeployError(Exception):
    """Anything that should stop the deploy with a readable message."""


def read_source(path):
    if not os.path.isfile(path):
        raise DeployError(f"bundled artwork missing: {path}")
    with open(path, "rb") as fh:
        data = fh.read()
    if not data:
        raise DeployError(f"bundled artwork is empty: {path}")
    return data


def check_png(data, where):
    """Validate PNG magic, IHDR dimensions and the byte budget."""
    if len(data) < 33:
        raise DeployError(f"{where}: only {len(data)} bytes, too short to be a PNG")
    if data[:8] != MAGIC:
        raise DeployError(f"{where}: not a PNG (header {data[:8]!r})")
    if data[12:16] != IHDR:
        raise DeployError(f"{where}: first chunk is {data[12:16]!r}, expected IHDR")
    w, h = struct.unpack(">II", data[16:24])
    if (w, h) != (SIDE, SIDE):
        raise DeployError(f"{where}: image is {w}x{h}, expected {SIDE}x{SIDE}")
    if len(data) > MAX_BYTES:
        raise DeployError(
            f"{where}: {len(data):,} bytes exceeds the "
            f"{MAX_BYTES:,}-byte limit by {len(data) - MAX_BYTES:,}"
        )
    return len(data)


def deploy(src, out_dir):
    data = read_source(src)
    src_bytes = check_png(data, f"source {src}")

    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        raise DeployError(f"cannot create output directory {out_dir}: {exc}") from exc
    if not os.path.isdir(out_dir):
        raise DeployError(f"output path is not a directory: {out_dir}")

    dest = os.path.join(out_dir, NAME)
    fd, tmp = tempfile.mkstemp(prefix=".entry-", suffix=".png.tmp", dir=out_dir)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o644)          # mkstemp gives 0600; grading needs 0644

        # Re-read what actually landed on disk before publishing it.
        with open(tmp, "rb") as fh:
            staged = fh.read()
        check_png(staged, f"staged {tmp}")
        if staged != data:
            raise DeployError(f"staged file does not match source ({tmp})")

        os.replace(tmp, dest)         # atomic within one filesystem
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

    with open(dest, "rb") as fh:
        final = fh.read()
    final_bytes = check_png(final, f"deployed {dest}")
    if final_bytes != src_bytes:
        raise DeployError(f"deployed size {final_bytes:,} != source {src_bytes:,}")

    mode = os.stat(dest).st_mode & 0o777
    if mode != 0o644:
        raise DeployError(f"deployed mode is {mode:04o}, expected 0644")

    return dest, final_bytes, mode


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, NAME)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"

    try:
        dest, size, mode = deploy(src, out_dir)
    except DeployError as exc:
        print(f"deploy failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"deploy failed: {exc}", file=sys.stderr)
        return 1

    print(f"deployed {src}")
    print(f"      -> {dest}")
    print(f"      {size:,} bytes, mode {mode:04o}, {SIDE}x{SIDE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
