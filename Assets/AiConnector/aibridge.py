def callAiAgent(evidence):
    try:
        from Ai.chatandagents.agent import evaluate as aiEvaluate
        return aiEvaluate(evidence)
    except Exception as exc:
        return {
            "verdict": "Inconclusive",
            "evidenceSummary": [],
            "reasoningSummary": [],
            "conclusion": f"Evaluation error: {exc}"
        }


def formatReport(evidence, aiResult):
    lines = []
    lines.append(f"File: {evidence.get('path')}")
    lines.append(f"Type: {evidence.get('fileType', evidence.get('format', 'unknown'))}")

    sizeBytes = evidence.get("sizeBytes")
    if sizeBytes is not None:
        lines.append(f"Size: {sizeBytes:,} bytes")

    hashes = evidence.get("hashes")
    if hashes and isinstance(hashes, dict):
        lines.append(f"SHA256: {hashes.get('sha256')}")

    lines.append("")
    lines.append(f"Verdict: {aiResult.get('verdict', 'Unknown')}")

    evidenceSummary = aiResult.get("evidenceSummary") or []
    if evidenceSummary:
        lines.append("")
        lines.append("Evidence:")
        for item in evidenceSummary:
            lines.append(f"  - {item}")

    reasoningSummary = aiResult.get("reasoningSummary") or []
    if reasoningSummary:
        lines.append("")
        lines.append("Reasoning:")
        for item in reasoningSummary:
            lines.append(f"  - {item}")

    lines.append("")
    lines.append(f"Conclusion: {aiResult.get('conclusion', '')}")

    analysisErrors = evidence.get("errors") or []
    if analysisErrors:
        lines.append("")
        lines.append("Notes:")
        for item in analysisErrors:
            lines.append(f"  - {item}")

    return "\n".join(lines)
