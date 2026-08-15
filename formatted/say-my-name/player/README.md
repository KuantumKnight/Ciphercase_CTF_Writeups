# Say My Name

**Author:** KuantumKnight
**Category:** AI / Model Inversion
**Difficulty:** Medium–Hard

The DEA recovered an experimental identity-classification model from
an abandoned Madrigal workstation.  The supplied documentation lists
four identities:

    index 0 = Walter
    index 1 = Jesse
    index 2 = Gus
    index 3 = Mike

The model has a fifth output.  Its identity is undocumented.

FEATURE PIPELINE

The profiler accepts 32 raw unsigned-byte measurements normalized to
[0, 1].  The normalization used by the original pipeline was:

    normalized = raw / 255

The included sample is an ordinary input.  Query it with:

    python3 run.py

The model is intentionally provided without server-side code.  Inspect
the ONNX graph and its computation paths.

**Flag format:** `CYS{...}`
