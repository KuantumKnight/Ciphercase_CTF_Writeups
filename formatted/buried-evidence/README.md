# Buried Evidence

| Field | Value |
| --- | --- |
| Author | KuantumKnight |
| Category | Forensics |
| Difficulty | Medium |
| Flag format | `CYS{...}` |

## Description

A damaged SD card was recovered from a warehouse security camera.

Investigators believe one piece of evidence was intentionally deleted before
the card was seized. Recover the deleted evidence and submit the flag
contained within it.

Provided artifact: `player/camera_sd.img`

Work from a copy of the forensic image and avoid mounting it read/write.

## Package layout

- `player/` — files distributed to contestants.
- `organizer/` — private authoring material, hints, verifier, and solution.

Do not distribute `organizer/` with the player package.
