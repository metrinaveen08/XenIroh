"""
Assets/ImageAnalyzer.py

Static analysis of image files. Never executes/renders anything beyond
reading pixel and metadata bytes.

Responsibility: collect EVIDENCE about an image (format, dimensions, EXIF,
trailing/appended data, LSB entropy anomalies). This module does NOT decide
whether the image is carrying a steganographic payload - that judgement
belongs to AI/agent.py.

Note on steganography detection: there is no single check that proves an
image contains hidden data. What we can do statically is surface INDICATORS
that make hidden data more or less likely, and let the AI's probability
reasoning (Unit V) combine them:
    - data appended after the image's official end-of-file marker
    - unusually high entropy in the least-significant bits of pixel data
      (real photos have some LSB randomness from sensor noise, but
      LSB-steganography tends to push it close to true randomness)
    - EXIF/metadata inconsistent with the declared format

Evidence contract:
    analyzeImage(path) -> dict, always containing at least:
        {
            "path": str,
            "exists": bool,
            "isImage": bool,
            "format": str | None,
            "dimensions": [w, h] | None,
            "sizeBytes": int | None,
            "exif": dict,
            "trailingDataBytes": int,       # bytes found after EOF marker
            "lsbEntropy": float | None,     # 0..8, higher = more random
            "errors": list[str],
        }
"""

import math
import os
from collections import Counter

try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# Known end-of-image markers so we can detect trailing/appended data -
# a classic way to smuggle a second payload inside an image file.
EOF_MARKERS = {
    "JPEG": b"\xff\xd9",
    "PNG": b"\x49\x45\x4e\x44\xae\x42\x60\x82",  # IEND chunk + CRC
}


def readExif(image):
    exifData = {}
    if not HAS_PIL:
        return exifData
    try:
        raw = image.getexif()
        if not raw:
            return exifData
        for tagId, value in raw.items():
            tagName = ExifTags.TAGS.get(tagId, str(tagId))
            try:
                exifData[tagName] = str(value)
            except Exception:
                exifData[tagName] = "<unreadable>"
    except Exception:
        pass
    return exifData


def findTrailingDataBytes(path, imageFormat):
    marker = EOF_MARKERS.get(imageFormat)
    if marker is None:
        return 0

    try:
        with open(path, "rb") as fileHandle:
            data = fileHandle.read()
    except Exception:
        return 0

    idx = data.rfind(marker)
    if idx == -1:
        return 0

    trailingStart = idx + len(marker)
    return max(0, len(data) - trailingStart)


def computeLsbEntropy(image, sampleLimit=200_000):
    """Shannon entropy (bits) of the least-significant bit plane across
    pixel channels. Near 8.0 for byte-level entropy calcs isn't meaningful
    here since we only look at 1 bit per channel; instead this reports the
    entropy of the LSB *bit stream* (max 1.0 bit per bit, so we report over
    a window of bits reconstructed as bytes for a comparable 0..8 scale).
    """
    try:
        rgbImage = image.convert("RGB")
    except Exception:
        return None

    pixels = list(rgbImage.getdata())
    if len(pixels) > sampleLimit:
        step = len(pixels) // sampleLimit
        pixels = pixels[::max(step, 1)]

    lsbBits = []
    for r, g, b in pixels:
        lsbBits.append(r & 1)
        lsbBits.append(g & 1)
        lsbBits.append(b & 1)

    # Pack bits into bytes so we get a standard 0..8 bits-of-entropy figure.
    lsbBytes = []
    for i in range(0, len(lsbBits) - 7, 8):
        byteVal = 0
        for bitOffset in range(8):
            byteVal = (byteVal << 1) | lsbBits[i + bitOffset]
        lsbBytes.append(byteVal)

    if not lsbBytes:
        return None

    counts = Counter(lsbBytes)
    total = len(lsbBytes)
    entropy = 0.0
    for count in counts.values():
        probability = count / total
        entropy -= probability * math.log2(probability)

    return round(entropy, 4)


def analyzeImage(path):
    evidence = {
        "path": path,
        "exists": os.path.isfile(path),
        "isImage": False,
        "format": None,
        "dimensions": None,
        "sizeBytes": None,
        "exif": {},
        "trailingDataBytes": 0,
        "lsbEntropy": None,
        "errors": [],
    }

    if not evidence["exists"]:
        evidence["errors"].append("File does not exist.")
        return evidence

    try:
        evidence["sizeBytes"] = os.path.getsize(path)
    except Exception as exc:
        evidence["errors"].append(f"size: {exc}")

    if not HAS_PIL:
        evidence["errors"].append("Pillow not installed; image analysis skipped.")
        return evidence

    try:
        image = Image.open(path)
        image.verify()
        # verify() invalidates the image object for further use, so reopen.
        image = Image.open(path)
    except Exception as exc:
        evidence["errors"].append(f"open/verify: {exc}")
        return evidence

    evidence["isImage"] = True
    evidence["format"] = image.format
    evidence["dimensions"] = list(image.size)

    try:
        evidence["exif"] = readExif(image)
    except Exception as exc:
        evidence["errors"].append(f"exif: {exc}")

    try:
        evidence["trailingDataBytes"] = findTrailingDataBytes(path, image.format)
    except Exception as exc:
        evidence["errors"].append(f"trailing-data: {exc}")

    try:
        evidence["lsbEntropy"] = computeLsbEntropy(image)
    except Exception as exc:
        evidence["errors"].append(f"lsb-entropy: {exc}")

    return evidence


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python ImageAnalyzer.py <path-to-image>")
        sys.exit(1)

    result = analyzeImage(sys.argv[1])
    print(json.dumps(result, indent=2, default=str))
