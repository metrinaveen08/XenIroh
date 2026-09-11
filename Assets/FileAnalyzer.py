"""
Assets/FileAnalyzer.py

Static analysis of files. Never executes the sample.

Responsibility: collect raw EVIDENCE about a file (type, hashes, structure,
embedded code, suspicious strings). This module does NOT decide whether
something is malicious - that judgement belongs to AI/agent.py, which
reasons over the evidence dict this module returns.

Evidence contract:
    analyzeFile(path) -> dict, always containing at least:
        {
            "path": str,
            "exists": bool,
            "fileType": str | None,
            "sizeBytes": int | None,
            "hashes": {"md5": str, "sha1": str, "sha256": str} | None,
            "peInfo": dict | None,        # only if PE executable
            "officeInfo": dict | None,    # only if Office doc w/ macros
            "pdfInfo": dict | None,       # only if PDF
            "suspiciousStrings": list[str],
            "errors": list[str],          # non-fatal problems while analyzing
        }
"""

import hashlib
import os
import re

# Optional third-party libs. Each is wrapped so XenIroh degrades gracefully
# (with a note in "errors") if a package isn't installed yet, rather than
# crashing the whole analysis.
try:
    import magic  # python-magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    import filetype
    HAS_FILETYPE = True
except ImportError:
    HAS_FILETYPE = False

try:
    import pefile
    HAS_PEFILE = True
except ImportError:
    HAS_PEFILE = False

try:
    from oletools.olevba import VBA_Parser
    HAS_OLETOOLS = True
except ImportError:
    HAS_OLETOOLS = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# A short list of strings that are commonly seen in malicious documents/
# scripts. This is intentionally simple pattern matching - it produces
# EVIDENCE for the AI layer, it is not itself a classifier.
SUSPICIOUS_PATTERNS = [
    rb"powershell",
    rb"-enc(oded)?command",
    rb"Invoke-Expression",
    rb"cmd\.exe",
    rb"WScript\.Shell",
    rb"Shell\(",
    rb"AutoOpen",
    rb"Document_Open",
    rb"CreateObject",
    rb"URLDownloadToFile",
    rb"regsvr32",
    rb"mshta",
    rb"certutil",
    rb"base64",
]


def hashFile(path, chunkSize=1024 * 1024):
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    with open(path, "rb") as fileHandle:
        while True:
            chunk = fileHandle.read(chunkSize)
            if not chunk:
                break
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)

    return {
        "md5": md5.hexdigest(),
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }


def detectFileType(path):
    if HAS_MAGIC:
        try:
            return magic.from_file(path)
        except Exception:
            pass
    if HAS_FILETYPE:
        try:
            guess = filetype.guess(path)
            if guess is not None:
                return f"{guess.mime} ({guess.extension})"
        except Exception:
            pass
    # Last-resort fallback: extension only, clearly labelled as unverified.
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return f"unknown (extension only: .{ext})" if ext else "unknown"


def scanSuspiciousStrings(path, maxHits=25):
    hits = []
    try:
        with open(path, "rb") as fileHandle:
            data = fileHandle.read()
    except Exception:
        return hits

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, data, re.IGNORECASE):
            hits.append(pattern.decode(errors="ignore"))
            if len(hits) >= maxHits:
                break
    return hits


def analyzePe(path):
    """PE (Windows executable) structural evidence. Returns None if not a PE
    or pefile isn't installed."""
    if not HAS_PEFILE:
        return None
    try:
        pe = pefile.PE(path, fast_load=True)
    except pefile.PEFormatError:
        return None
    except Exception:
        return None

    try:
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
    except Exception:
        pass

    importedApis = []
    try:
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dllName = entry.dll.decode(errors="ignore") if entry.dll else "?"
                for imp in entry.imports:
                    if imp.name:
                        importedApis.append(f"{dllName}:{imp.name.decode(errors='ignore')}")
    except Exception:
        pass

    peInfo = {
        "isPe": True,
        "isDll": pe.is_dll(),
        "isExe": pe.is_exe(),
        "machine": hex(pe.FILE_HEADER.Machine),
        "numberOfSections": pe.FILE_HEADER.NumberOfSections,
        "timestamp": pe.FILE_HEADER.TimeDateStamp,
        "importedApiCount": len(importedApis),
        "importedApisSample": importedApis[:40],
        "sections": [
            {
                "name": section.Name.decode(errors="ignore").strip("\x00"),
                "virtualSize": section.Misc_VirtualSize,
                "rawSize": section.SizeOfRawData,
                "entropy": round(section.get_entropy(), 3),
            }
            for section in pe.sections
        ],
    }
    pe.close()
    return peInfo


def analyzeOfficeDoc(path):
    """VBA macro evidence for Office documents. Returns None if not an
    Office doc or oletools isn't installed."""
    if not HAS_OLETOOLS:
        return None
    try:
        parser = VBA_Parser(path)
    except Exception:
        return None

    try:
        if not parser.detect_vba_macros():
            parser.close()
            return {"hasMacros": False}

        autoExecKeywords = []
        suspiciousKeywords = []
        try:
            for kwType, keyword, _description in parser.analyze_macros():
                if kwType == "AutoExec":
                    autoExecKeywords.append(keyword)
                elif kwType == "Suspicious":
                    suspiciousKeywords.append(keyword)
        except Exception:
            pass

        officeInfo = {
            "hasMacros": True,
            "autoExecKeywords": list(set(autoExecKeywords)),
            "suspiciousKeywords": list(set(suspiciousKeywords)),
        }
    finally:
        parser.close()

    return officeInfo


def analyzePdf(path):
    """PDF structural evidence (embedded JS, launch actions). Returns None
    if not a PDF or PyMuPDF isn't installed."""
    if not HAS_PYMUPDF:
        return None
    try:
        doc = fitz.open(path)
    except Exception:
        return None
    if doc.is_pdf is False:
        doc.close()
        return None

    embeddedJs = []
    try:
        xrefCount = doc.xref_length()
        for xref in range(1, xrefCount):
            try:
                obj = doc.xref_object(xref)
            except Exception:
                continue
            if obj and "/JS" in obj:
                embeddedJs.append(xref)
    except Exception:
        pass

    pdfInfo = {
        "isPdf": True,
        "pageCount": doc.page_count,
        "hasEmbeddedJavaScript": len(embeddedJs) > 0,
        "javaScriptObjectCount": len(embeddedJs),
        "isEncrypted": doc.is_encrypted,
    }
    doc.close()
    return pdfInfo


def analyzeFile(path):
    evidence = {
        "path": path,
        "exists": os.path.isfile(path),
        "fileType": None,
        "sizeBytes": None,
        "hashes": None,
        "peInfo": None,
        "officeInfo": None,
        "pdfInfo": None,
        "suspiciousStrings": [],
        "errors": [],
    }

    if not evidence["exists"]:
        evidence["errors"].append("File does not exist.")
        return evidence

    try:
        evidence["sizeBytes"] = os.path.getsize(path)
    except Exception as exc:
        evidence["errors"].append(f"size: {exc}")

    try:
        evidence["hashes"] = hashFile(path)
    except Exception as exc:
        evidence["errors"].append(f"hash: {exc}")

    try:
        evidence["fileType"] = detectFileType(path)
    except Exception as exc:
        evidence["errors"].append(f"filetype: {exc}")

    try:
        evidence["suspiciousStrings"] = scanSuspiciousStrings(path)
    except Exception as exc:
        evidence["errors"].append(f"strings: {exc}")

    try:
        evidence["peInfo"] = analyzePe(path)
    except Exception as exc:
        evidence["errors"].append(f"pe: {exc}")

    try:
        evidence["officeInfo"] = analyzeOfficeDoc(path)
    except Exception as exc:
        evidence["errors"].append(f"office: {exc}")

    try:
        evidence["pdfInfo"] = analyzePdf(path)
    except Exception as exc:
        evidence["errors"].append(f"pdf: {exc}")

    if not HAS_MAGIC and not HAS_FILETYPE:
        evidence["errors"].append(
            "Neither python-magic nor filetype is installed; file type is unverified."
        )
    if not HAS_PEFILE:
        evidence["errors"].append("pefile not installed; PE analysis skipped.")
    if not HAS_OLETOOLS:
        evidence["errors"].append("oletools not installed; macro analysis skipped.")
    if not HAS_PYMUPDF:
        evidence["errors"].append("PyMuPDF not installed; PDF analysis skipped.")

    return evidence


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 2:
        print("Usage: python FileAnalyzer.py <path-to-file>")
        sys.exit(1)

    result = analyzeFile(sys.argv[1])
    print(json.dumps(result, indent=2, default=str))
