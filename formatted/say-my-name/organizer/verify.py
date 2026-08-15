#!/usr/bin/env python3
"""Release checks for the packaged player artifact."""

from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from onnx import numpy_helper


ROOT = Path(__file__).resolve().parents[1]
PLAYER = ROOT / "player"
EXPECTED = b"CYS{Y0UR3_G0DD4MN_R1GHT_ABQKQF!}"


def main() -> None:
    model_path = PLAYER / "heisenberg.onnx"
    model = onnx.load(model_path)
    onnx.checker.check_model(model)
    tensors = {item.name: numpy_helper.to_array(item) for item in model.graph.initializer}

    matrix = tensors["fc1.weight"].astype(np.float64)
    bias = tensors["fc1.bias"].astype(np.float64)
    target = tensors["buffer_0"].astype(np.float64)
    normalized = np.linalg.lstsq(matrix, np.arctanh(target) - bias, rcond=None)[0]
    recovered = bytes(np.rint(normalized * 255).astype(np.uint8))
    assert recovered == EXPECTED, recovered
    assert matrix.shape == (48, 32)
    assert np.linalg.matrix_rank(matrix) == 32

    session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
    sample = np.load(PLAYER / "sample.npy").astype(np.float32).reshape(1, -1)
    ordinary = session.run(None, {"input": sample})[0]
    secret = session.run(None, {"input": normalized.astype(np.float32)[None, :]})[0]
    assert ordinary.shape == (1, 5)
    assert np.isclose(ordinary.sum(), 1.0)
    assert secret[0, 4] > 0.999999

    print("ONNX checker: PASS")
    print("exact inversion: PASS")
    print("sample shape/output: PASS")
    print("hidden-class activation: PASS")
    print(f"recovered: {recovered.decode()}")


if __name__ == "__main__":
    main()
