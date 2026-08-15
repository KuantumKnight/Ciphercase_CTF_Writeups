# Say My Name

| Field | Value |
| --- | --- |
| Author | KuantumKnight |
| Category | AI / Model Inversion |
| Difficulty | Medium–Hard |
| Flag format | `CYS{...}` |

## Description

The DEA recovered an experimental identity-classification model from an
abandoned Madrigal workstation. Its documentation lists four identities:

`Walter`, `Jesse`, `Gus`, and `Mike`.

Except the model has **five outputs**. There is no record of the fifth class,
no sample belonging to it, and no label explaining who—or what—it represents.

All you have is the recovered ONNX model, one sample input, and a local
runner. The model already knows the answer.

Make it say his name.

## Package layout

- `player/` — files distributed to contestants.
- `organizer/` — private hints, generator, verifier, and solution.

Do not distribute `organizer/` with the player package.
