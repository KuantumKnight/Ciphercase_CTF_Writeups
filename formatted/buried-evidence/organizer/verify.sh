#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${1:-$ROOT_DIR/../player/camera_sd.img}"
PARTITION_OFFSET=2048
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for tool in fls icat exiftool 7z file strings grep awk cmp identify; do
  command -v "$tool" >/dev/null || {
    printf 'Missing required tool: %s\n' "$tool" >&2
    exit 1
  }
done

[[ -f "$IMAGE" ]] || {
  printf 'Missing artifact: %s\n' "$IMAGE" >&2
  exit 1
}

LIST="$(fls -r -o "$PARTITION_OFFSET" "$IMAGE")"

inode_for() {
  local expression="$1"
  printf '%s\n' "$LIST" | awk -v expression="$expression" '
    $0 ~ expression {
      inode = ($3 == "*" ? $4 : $3)
      sub(/:$/, "", inode)
      print inode
      exit
    }
  '
}

EXIF_INODE="$(inode_for 'IMG_0383[.]JPG$')"
BARCODE_INODE="$(inode_for 'barcode_map[.]txt$')"
JPEG_INODE="$(inode_for '[*].*0387[.]JPG$')"
ARCHIVE_INODE="$(inode_for '[*].*EVID_2317[.]DAT$')"
CONFIG_INODE="$(inode_for 'CONFIG[.]TXT$')"

for value in EXIF_INODE BARCODE_INODE JPEG_INODE ARCHIVE_INODE CONFIG_INODE; do
  [[ -n "${!value}" ]] || {
    printf 'Could not locate expected entry: %s\n' "$value" >&2
    exit 1
  }
done

icat -o "$PARTITION_OFFSET" "$IMAGE" "$EXIF_INODE" > "$TMP_DIR/IMG_0383.JPG"
icat -o "$PARTITION_OFFSET" "$IMAGE" "$BARCODE_INODE" > "$TMP_DIR/barcode_map.txt"
icat -o "$PARTITION_OFFSET" "$IMAGE" "$JPEG_INODE" > "$TMP_DIR/IMG_0387.JPG"
icat -o "$PARTITION_OFFSET" "$IMAGE" "$ARCHIVE_INODE" > "$TMP_DIR/EVID_2317.DAT"
icat -o "$PARTITION_OFFSET" "$IMAGE" "$CONFIG_INODE" > "$TMP_DIR/CONFIG.TXT"

EXIF_COMMENT="$(exiftool -s3 -UserComment "$TMP_DIR/IMG_0383.JPG")"
grep -Fq 'QA TEST TOKEN: CYS{N0TH1NG_T0_S33_H3R3}' <<<"$EXIF_COMMENT"
grep -Fq 'verification=CYS{TH3_B4RC0D3_L13S}' "$TMP_DIR/barcode_map.txt"
grep -Fq 'DEVICE=CAM07' "$TMP_DIR/CONFIG.TXT"
grep -Fq 'ARCHIVE_SCHEME=<DEVICE>-<LOT>-<HHMMSS>' "$TMP_DIR/CONFIG.TXT"

exiftool -b -ThumbnailImage "$TMP_DIR/IMG_0387.JPG" > "$TMP_DIR/thumbnail.jpg"
[[ -s "$TMP_DIR/thumbnail.jpg" ]]
[[ "$(identify -format '%wx%h' "$TMP_DIR/thumbnail.jpg")" == '1200x800' ]]

7z t -pCAM07-2317-221743 "$TMP_DIR/EVID_2317.DAT" >/dev/null
mkdir "$TMP_DIR/extracted"
7z x -y -pCAM07-2317-221743 -o"$TMP_DIR/extracted" "$TMP_DIR/EVID_2317.DAT" >/dev/null
grep -Fxq 'CYS{TH3_THUMBNA1L_R3M3MB3R3D}' "$TMP_DIR/extracted/evidence.txt"

if strings -a "$IMAGE" | grep -Fq 'CYS{TH3_THUMBNA1L_R3M3MB3R3D}'; then
  printf 'Final flag leaked in plaintext in raw image.\n' >&2
  exit 1
fi

printf 'PASS: decoys, deleted evidence, thumbnail, archive, and final flag verified.\n'
