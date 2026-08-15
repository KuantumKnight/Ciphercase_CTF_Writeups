# Buried Evidence — Intended Solution

## 1. Identify the partition

The supplied artifact is a raw MBR disk image. `mmls` shows a FAT32 partition
starting at sector 2048.

```text
mmls camera_sd.img
fls -r -o 2048 camera_sd.img
```

The recursive listing contains two deleted entries in `DCIM/100CAM/`:

```text
EVID_2317.DAT
IMG_0387.JPG
```

Recover them with their inode numbers from `fls`:

```text
icat -o 2048 camera_sd.img <IMG_0387_inode> > IMG_0387.JPG
icat -o 2048 camera_sd.img <EVID_2317_inode> > EVID_2317.DAT
```

## 2. Inspect the recovered JPEG thumbnail

The visible image is an ordinary warehouse frame, but its EXIF contains an
embedded thumbnail. Extract it with:

```text
exiftool -b -ThumbnailImage IMG_0387.JPG > thumbnail.jpg
```

The thumbnail shows:

```text
DEVICE: CAM07
LOT: 2317
EVID_2317
```

This points to the deleted archive rather than being the flag itself.

## 3. Derive the archive password

Recover the live configuration file from `SYSTEM/CONFIG.TXT` and inspect it.
It specifies the archive naming scheme:

```text
ARCHIVE_SCHEME=<DEVICE>-<LOT>-<HHMMSS>
```

The device and lot come from the thumbnail. The timestamp comes from the
recovered camera JPEG metadata:

```text
DateTimeOriginal: 2026:08:17 22:17:43
```

Therefore the archive password is:

```text
CAM07-2317-221743
```

Test and extract the archive:

```text
7z t -pCAM07-2317-221743 EVID_2317.DAT
7z x -pCAM07-2317-221743 EVID_2317.DAT
```

The recovered `evidence.txt` contains the final flag:

```text
CYS{TH3_THUMBNA1L_R3M3MB3R3D}
```

## Intentional decoys

`IMG_0383.JPG` contains this EXIF user comment:

```text
QA TEST TOKEN: CYS{N0TH1NG_T0_S33_H3R3}
```

`SYSTEM/barcode_map.txt` contains a plausible warehouse lookup route ending
in:

```text
CYS{TH3_B4RC0D3_L13S}
```

Both are intentionally discoverable, but neither is inside the deleted
evidence archive. The challenge prompt requires recovering the deleted
evidence and submitting the flag contained within it.
