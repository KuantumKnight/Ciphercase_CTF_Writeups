# Blue Noise

| Field | Value |
| --- | --- |
| Author | KuantumKnight |
| Category | Forensics / Steganography |
| Difficulty | Medium |
| Flag format | `CYS{...}` |

## Description

The visible photograph is only a distraction. Inspect the supplied PNG for
hidden information, recover the key, and use it to unlock the appended
artifact.

The intended solve chain is concealed in the image itself. Recover the flag
from the player artifact `player/blue_noise.png`.

## Package layout

- `player/` — files distributed to contestants.
- `organizer/` — private assets, generator, hints, verifier, and solution.

Do not distribute `organizer/` with the player package.
