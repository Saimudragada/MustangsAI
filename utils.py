import re

def basic_clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def truncate(text: str, n: int = 220) -> str:
    return (text[: n - 1] + "…") if len(text) > n else text
