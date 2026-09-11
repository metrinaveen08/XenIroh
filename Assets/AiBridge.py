"""
Assets/AiBridge.py

Single call site for handing static-analysis evidence to AI/agent.py and
formatting the result as a human-readable report. Both the manual
analyzer window (GUI/XenIroh.py) and the background watcher
(Watcher/watcher.py) go through this, so there is exactly one place that
knows how to talk to the AI layer.
"""


def callAiAgent(evidence):
    """Expected AI/agent.py contract (implement this function there):

        def evaluate(evidence: dict) -> dict:
            return {
                "verdict": "Suspicious" | "Likely Safe" | "Inconclusive",
                "evidenceSummary": [str, ...],
                "reasoningSummary": [str, ...],
                "conclusion": str,
            }
    """
    try:
        from AI.agent import evaluate as aiEvaluate
    except ImportError:
        return {
            "verdict": "Inconclusive",
            "evidenceSummary": ["AI/agent.py not implemented yet."],
            "reasoningSummary": [],
            "conclusion": (
                "Static evidence was collected, but no AI reasoning is wired up yet. "
                "Implement AI/agent.py's evaluate(evidence) to get a verdict."
            ),
        }

    try:
        return aiEvaluate(evidence)
    except Exception as exc:
        return {
            "verdict": "Inconclusive",
            "evidenceSummary": [],
            "reasoningSummary": [],
            "conclusion": f"AI reasoning raised an error: {exc}",
        }


def formatReport(evidence, aiResult):
    lines = []
    lines.append(f"File: {evidence.get('path')}")
    lines.append(f"Type: {evidence.get('fileType', evidence.get('format', 'unknown'))}")

    sizeBytes = evidence.get("sizeBytes")
    if sizeBytes is not None:
        lines.append(f"Size: {sizeBytes:,} bytes")

    hashes = evidence.get("hashes")
    if hashes:
        lines.append(f"SHA256: {hashes['sha256']}")

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
        lines.append("Analysis notes:")
        for item in analysisErrors:
            lines.append(f"  - {item}")

    return "\n".join(lines)
