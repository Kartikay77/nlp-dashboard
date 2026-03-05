import re

STOPWORDS = {
    "the","a","an","is","are","to","of","and","in","for","on","at","with","this","that",
    "it","be","as","by","from","or","we","you","i","they","he","she","was","were","am",
    "will","can","could","should","would","have","has","had","do","does","did","our",
    "your","their","my","me","us","them"
}


def clean_text(text: str) -> str:
    text = str(text or "").lower()
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s%$#@:/\.-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [t for t in text.split() if t not in STOPWORDS]
    return " ".join(tokens)