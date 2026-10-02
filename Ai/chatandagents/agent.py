import os

SUSPICIOUS_EXTENSIONS = {
    ".exe", ".scr", ".bat", ".cmd", ".vbs", ".vbe", ".js", ".jse",
    ".wsf", ".wsh", ".ps1", ".psm1", ".dll", ".hta", ".pif", ".cpl"
}


def evaluate(evidence):
    path = evidence.get("path", "")
    fileName = os.path.basename(path)
    base, ext = os.path.splitext(fileName)
    extLower = ext.lower()

    evidenceSummary = []
    reasoningSummary = []
    suspiciousScore = 0

    if not evidence.get("exists", False):
        return {
            "verdict": "Inconclusive",
            "evidenceSummary": ["Target file does not exist on disk."],
            "reasoningSummary": [],
            "conclusion": "File was missing or removed before inspection could finish."
        }

    evidenceSummary.append(f"File: {fileName}")
    fileSize = evidence.get("sizeBytes")
    if fileSize is not None:
        evidenceSummary.append(f"Size: {fileSize:,} bytes")

    # Double extension check
    parts = fileName.lower().split(".")
    if len(parts) > 2 and f".{parts[-1]}" in SUSPICIOUS_EXTENSIONS:
        suspiciousScore += 3
        reasoningSummary.append("Deceptive double extension detected.")

    # Suspicious strings
    matchedStrings = evidence.get("suspiciousStrings", [])
    if matchedStrings:
        suspiciousScore += len(matchedStrings) * 2
        for s in matchedStrings[:5]:
            reasoningSummary.append(f"Contains risky keyword: {s}")

    # PE Executable checks
    peInfo = evidence.get("peInfo")
    if peInfo and peInfo.get("isPe"):
        evidenceSummary.append(f"Executable (sections: {peInfo.get('numberOfSections', 0)})")
        sections = peInfo.get("sections", [])
        for sec in sections:
            name = sec.get("name", "").lower()
            entropy = sec.get("entropy", 0)
            if "upx" in name:
                suspiciousScore += 3
                reasoningSummary.append(f"Packed PE section detected: {name}")
            if entropy > 7.2:
                suspiciousScore += 2
                reasoningSummary.append(f"High-entropy encrypted/compressed section ({sec.get('name')}: {entropy})")

    # Office macros
    officeInfo = evidence.get("officeInfo")
    if officeInfo and officeInfo.get("hasMacros"):
        autoExec = officeInfo.get("autoExecKeywords", [])
        suspiciousKw = officeInfo.get("suspiciousKeywords", [])
        if autoExec:
            suspiciousScore += 3
            reasoningSummary.append(f"Auto-executing macros found: {', '.join(autoExec)}")
        if suspiciousKw:
            suspiciousScore += 2
            reasoningSummary.append(f"Suspicious VBA functions: {', '.join(suspiciousKw[:4])}")

    # PDF embedded script
    pdfInfo = evidence.get("pdfInfo")
    if pdfInfo and pdfInfo.get("hasEmbeddedJavaScript"):
        suspiciousScore += 3
        reasoningSummary.append("PDF contains embedded JavaScript streams.")

    # Image payload indicators
    if evidence.get("isImage"):
        trailing = evidence.get("trailingDataBytes", 0)
        entropy = evidence.get("lsbEntropy")
        if trailing > 128:
            suspiciousScore += 2
            reasoningSummary.append(f"Appended trailing data after EOF marker: {trailing} bytes")
        if entropy is not None and entropy > 7.6:
            suspiciousScore += 2
            reasoningSummary.append(f"Unusually high LSB entropy: {entropy}")

    if suspiciousScore >= 3:
        verdict = "Suspicious"
        conclusion = "High-risk indicators or malicious patterns identified in file."
    elif suspiciousScore in (1, 2) or extLower in SUSPICIOUS_EXTENSIONS:
        verdict = "Inconclusive"
        conclusion = "Potential risk factors present; manual review advised."
    else:
        verdict = "Likely Safe"
        conclusion = "No significant risk indicators or anomalies detected."

    return {
        "verdict": verdict,
        "evidenceSummary": evidenceSummary,
        "reasoningSummary": reasoningSummary,
        "conclusion": conclusion,
    }
