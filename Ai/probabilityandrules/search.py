import re


def search_signatures(content, patterns):
    matches = []
    if isinstance(content, str):
        content = content.encode("utf-8", errors="ignore")

    for pat in patterns:
        if isinstance(pat, str):
            pat = pat.encode("utf-8", errors="ignore")
        if re.search(pat, content, re.IGNORECASE):
            matches.append(pat.decode("utf-8", errors="ignore"))
    return matches


def find_byte_subsequence(data, sub):
    if not data or not sub:
        return -1
    return data.find(sub)
