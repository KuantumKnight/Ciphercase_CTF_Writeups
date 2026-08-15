#!/usr/bin/env python3
"""Reference solve for organizers; run from a directory containing the image."""

from __future__ import annotations

import io
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image


BLUE_BIT = 2
QR_BOX = (64, 64, 394, 394)


def find_iend(data: bytes) -> int:
    offset = 8
    while True:
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        offset += length + 12
        if kind == b"IEND":
            return offset


def main() -> None:
    image_path = Path(sys.argv[1] if len(sys.argv) > 1 else "blue_noise.png")
    qr_path = Path("/tmp/blue_noise_qr.png")
    with Image.open(image_path) as image:
        blue = image.convert("RGB").getchannel("B")
        plane = blue.point(lambda value: 255 if ((value >> BLUE_BIT) & 1) else 0)
        plane.crop(QR_BOX).save(qr_path)

    result = subprocess.run(
        ["zbarimg", "--quiet", str(qr_path)], capture_output=True, text=True, check=True
    )
    key = result.stdout.strip().split(":", 1)[1]
    print(f"QR key: {key}")

    data = image_path.read_bytes()
    trailing = data[find_iend(data) :]
    with zipfile.ZipFile(io.BytesIO(trailing)) as archive:
        note = archive.read("note.txt", pwd=key.encode()).decode()
    print(note, end="")


if __name__ == "__main__":
    main()
