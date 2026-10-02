class Rule:
    def __init__(self, name, condition, action):
        self.name = name
        self.condition = condition
        self.action = action

    def test(self, context):
        try:
            return bool(self.condition(context))
        except Exception:
            return False


def build_default_ruleset():
    rules = [
        Rule(
            "block_double_extension",
            lambda c: c.get("doubleExtension", False),
            "flag_suspicious"
        ),
        Rule(
            "macro_autoexec_alert",
            lambda c: len(c.get("officeInfo", {}).get("autoExecKeywords", [])) > 0,
            "flag_suspicious"
        ),
        Rule(
            "embedded_js_alert",
            lambda c: c.get("pdfInfo", {}).get("hasEmbeddedJavaScript", False),
            "flag_suspicious"
        ),
    ]
    return rules


def evaluate_rules(rules, context):
    triggered = []
    for r in rules:
        if r.test(context):
            triggered.append(r.name)
    return triggered
