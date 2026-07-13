# Placeholder service for JD parsing – rule‑based keyword extraction

def parse_jd(jd_text: str) -> list:
    """Extract simple keywords from a job description.

    This naive implementation splits on whitespace and punctuation,
    lower‑cases tokens, and returns a unique list of alphanumeric words
    longer than two characters. In a real implementation you would
    apply more sophisticated NLP or domain‑specific heuristics.
    """
    import re
    # Keep only word characters, split on non‑word boundaries
    tokens = re.findall(r"\b\w{3,}\b", jd_text.lower())
    # Return unique keywords preserving order of first appearance
    seen = set()
    keywords = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            keywords.append(token)
    return keywords
