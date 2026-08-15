# Buried Evidence — Organizer Package

**Author:** KuantumKnight

The player package contains only the challenge prompt and camera_sd.img.
This directory contains the private author material, including the intended
solution, decoys, hints, requirements, verifier, and generator.

Contents
--------

solution.md       Intended solve path and final flag
hints.txt         Progressive player hints
requirements.txt  Runtime and authoring requirements
verify.sh         End-to-end artifact verification
generator/        Rebuildable challenge generator and author assets

Reference artifact SHA-256
--------------------------

4eee1268d8450221f41cb84dff293d125c32464c9af1f548a38320e136f6a524  camera_sd.img

To rebuild the packaged artifact:

    cd generator
    ./build_challenge.sh

Then copy the resulting generator/camera_sd.img into player/ if you intend to
distribute the rebuilt image.

To verify the distributed player artifact:

    ./verify.sh
