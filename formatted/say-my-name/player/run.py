#!/usr/bin/env python3
"""Query the recovered identity model with the bundled sample."""

from pathlib import Path

import numpy as np
import onnxruntime as ort


ROOT = Path(__file__).resolve().parent
session = ort.InferenceSession(str(ROOT / "heisenberg.onnx"), providers=["CPUExecutionProvider"])
sample = np.load(ROOT / "sample.npy").astype(np.float32).reshape(1, -1)
output = session.run(None, {"input": sample})[0]
print(output[0])
