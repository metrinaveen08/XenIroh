def welcome_message():
    return (
        "Hi — I'm XenIroh's local security guide. Choose or drop a file to "
        "analyze it, or ask me what a verdict, rule, or warning means. "
        "Files and messages remain strictly local to your machine."
    )


def respond(message, evidence=None, result=None):
    text = message.strip().lower()
    if not text:
        return "Type a question or select a file to analyze."

    if any(word in text for word in ("help", "what can", "how do")):
        return "I can explain file verdicts, suspicious indicators, and protection rules. Choose or drag a file into the window to begin."

    if any(word in text for word in ("setup", "rule", "protect", "security level")):
        return "You can configure protection rules, folder monitoring, and security settings directly from the Settings or Rules page."

    if any(word in text for word in ("verdict", "file", "wrong", "problem", "why")):
        if result is None:
            return "No file has been analyzed yet in this session. Select a file first."
        findings = result.get("evidenceSummary") or ["No high-risk static indicators were detected."]
        return f"Current verdict: {result.get('verdict', 'Unknown')}. " + " ".join(findings[:3])

    if evidence is not None and result is not None:
        return (
            f"For the current file, XenIroh reports {result.get('verdict', 'Unknown')}. "
            f"{result.get('conclusion', '')}"
        )

    return "Ask me about file verdicts, security rules, or how XenIroh static analysis works."


def analysis_message(evidence, result):
    findings = result.get("evidenceSummary") or []
    detail = " ".join(findings[:3]) if findings else "No high-risk indicators detected."
    return f"Analysis complete: {result.get('verdict', 'Unknown')}. {detail} {result.get('conclusion', '')}"
