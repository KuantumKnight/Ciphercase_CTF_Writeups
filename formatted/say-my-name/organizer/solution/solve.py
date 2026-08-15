#!/usr/bin/env python3
"""Organizer solution: invert the auxiliary hidden representation."""

from pathlib import Path

import numpy as np
import onnx
from onnx import numpy_helper


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "player" / "heisenberg.onnx"


def main() -> None:
    model = onnx.load(MODEL)
    tensors = {item.name: numpy_helper.to_array(item) for item in model.graph.initializer}

    matrix = tensors["fc1.weight"].astype(np.float64)
    bias = tensors["fc1.bias"].astype(np.float64)
    target = tensors["buffer_0"].astype(np.float64)

    normalized = np.linalg.lstsq(
        matrix,
        np.arctanh(target) - bias,
        rcond=None,
    )[0]
    raw = np.rint(normalized * 255).astype(np.uint8)
    print(bytes(raw).decode("ascii"))


if __name__ == "__main__":
    main()
