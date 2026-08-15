# Organizer Notes — Say My Name

**Author:** KuantumKnight

## Answer

`CYS{Y0UR3_G0DD4MN_R1GHT_ABQKQF!}`

The answer is exactly 32 bytes. The player input is normalized as `raw / 255`.

## Intended solve

The graph has a shared `Gemm -> Tanh` feature extractor and a normal four-class head. The fifth logit is computed by an auxiliary distance branch:

```text
h(x) = tanh(Ax + b)
d(x) = ||h(x) - target||^2
score_4(x) = 18 - 2500*d(x)
```

The useful initializers are deliberately named generically:

- `fc1.weight`: 48×32 matrix `A`
- `fc1.bias`: vector `b`
- `buffer_0`: hidden target representation

Since `A` has full column rank:

```python
x = lstsq(A, arctanh(buffer_0) - b)[0]
raw = rint(x * 255).astype(uint8)
```

This recovers the flag. Gradient ascent on the fifth logit is an alternative solve.

## Progressive hints

Use the files in `hints/` in order. Hint 4 is the rescue hint and effectively reveals the mathematical inversion.

## Difficulty and scoring

Recommended rating: medium, with a hard feel if contestants are expected to reverse the graph from only the ONNX artifact.

Suggested score: 300 points.

The challenge is self-contained and has no server-side attack surface.

## Release checklist

- Distribute only `player/`.
- Confirm `python3 player/run.py` executes with the contestant's runtime.
- Do not include this directory, the generator, or the solution in the player attachment.
- The player ONNX file should not contain the flag in `strings` output.
- Preserve `sample.npy`; it is intentionally an ordinary sample and not the answer.
