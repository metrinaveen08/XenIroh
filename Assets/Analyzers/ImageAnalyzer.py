import math
import os
from collections import Counter

try:
    from PIL import Image, ExifTags
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

EOF_MARKERS = {
    "JPEG": b"\xff\xd9",
    "PNG": b"\x49\x45\x4e\x44\xae\x42\x60\x82",
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
        with open(path, "rb") as f:
            data = f.read()
    except Exception:
        return 0

    idx = data.rfind(marker)
    if idx == -1:
        return 0

    trailingStart = idx + len(marker)
    return max(0, len(data) - trailingStart)


def computeLsbEntropy(image, sampleLimit=200_000):
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
        p = count / total
        entropy -= p * math.log2(p)

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
        evidence["errors"].append("Pillow not installed.")
        return evidence

    try:
        image = Image.open(path)
        image.verify()
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
