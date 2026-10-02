RULE_CATALOG = {
    "watch_downloads": {
        "title": "Watch downloads",
        "description": "Analyze newly downloaded files before you open them.",
        "areas": {"downloads"},
    },
    "watch_documents": {
        "title": "Inspect documents with macros",
        "description": "Raise an alert for Office documents with macros or auto-run behavior.",
        "areas": {"documents"},
    },
    "watch_removable_media": {
        "title": "Watch removable media",
        "description": "Analyze files copied from USB drives and other removable media.",
        "areas": {"removable_media"},
    },
    "watch_scripts": {
        "title": "Elevate script warnings",
        "description": "Treat scripts and command launchers as higher-risk inputs.",
        "areas": {"scripts"},
    },
    "inspect_images": {
        "title": "Inspect image payload indicators",
        "description": "Alert on appended data or possible hidden payload indicators in images.",
        "areas": {"images"},
    },
    "conservative_alerts": {
        "title": "Use conservative alerts",
        "description": "Notify you about ambiguous files rather than suppressing uncertain results.",
        "areas": set(),
    },
}

EXPERIENCE_LABELS = {
    "new": "New to security",
    "comfortable": "Comfortable with technology",
    "advanced": "Advanced / security-aware",
}


def recommend_rules(experience, protection_areas):
    areas = set(protection_areas)
    recommended = [
        rule_id
        for rule_id, rule in RULE_CATALOG.items()
        if rule["areas"] & areas
    ]

    if experience == "new" or len(areas) >= 3:
        recommended.append("conservative_alerts")

    if not recommended:
        recommended = ["watch_downloads", "conservative_alerts"]

    return list(dict.fromkeys(recommended))


def rules_for_ids(rule_ids):
    return [
        {
            "id": rule_id,
            "title": RULE_CATALOG[rule_id]["title"],
            "description": RULE_CATALOG[rule_id]["description"],
        }
        for rule_id in rule_ids
        if rule_id in RULE_CATALOG
    ]
