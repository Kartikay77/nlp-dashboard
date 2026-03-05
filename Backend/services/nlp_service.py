import re
from collections import Counter
from difflib import SequenceMatcher
from typing import List, Dict, Any

import pandas as pd

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "are",
    "was", "were", "be", "been", "being", "this", "that", "it", "as", "at", "by", "from",
    "but", "not", "no", "yes", "we", "you", "they", "he", "she", "i", "me", "my", "our",
    "your", "their", "them", "us", "can", "could", "should", "would", "will", "just",
    "have", "has", "had", "do", "does", "did", "if", "then", "than", "so", "such",
}

def _safe_text(x) -> str:
    if x is None:
        return ""
    return str(x)

def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["id", "source", "sender", "sender_role", "project_id", "datetime", "subject", "text"])

    out = df.copy()
    for col in ["id", "source", "sender", "sender_role", "project_id", "datetime", "subject", "text"]:
        if col not in out.columns:
            out[col] = None

    out["source"] = out["source"].fillna("").astype(str).str.lower().str.strip()
    out["sender"] = out["sender"].fillna("").astype(str)
    out["sender_role"] = out["sender_role"].fillna("").astype(str)
    out["project_id"] = out["project_id"].fillna("").astype(str)
    out["subject"] = out["subject"].fillna("").astype(str)
    out["text"] = out["text"].fillna("").astype(str)
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce")
    return out

def _contains_keyword(text: str, keyword: str, fuzzy_threshold: int = 80) -> bool:
    text = _safe_text(text).lower()
    kw = _safe_text(keyword).lower().strip()
    if not kw:
        return False
    if kw in text:
        return True
    words = text.split()
    kw_words = kw.split()
    win = max(1, len(kw_words))
    for i in range(0, max(1, len(words) - win + 1)):
        chunk = " ".join(words[i:i + win])
        ratio = int(SequenceMatcher(None, chunk, kw).ratio() * 100)
        if ratio >= fuzzy_threshold:
            return True
    return False

def apply_text_filters(df: pd.DataFrame, req=None, **kwargs) -> pd.DataFrame:
    """
    Fixed to handle both Pydantic 'req' objects and direct keyword arguments.
    """
    filtered_df = _normalize_df(df)
    if filtered_df.empty:
        return filtered_df

    # Helper to pull from req object OR kwargs
    def get_val(key, default=None):
        if req is not None:
            return getattr(req, key, default)
        return kwargs.get(key, default)

    req_sources = [str(s).strip().lower() for s in (get_val("sources", []) or []) if str(s).strip()]
    req_keywords = [str(k).strip() for k in (get_val("keywords", []) or []) if str(k).strip()]
    date_from = get_val("date_from")
    date_to = get_val("date_to")
    fuzzy_threshold = int(get_val("fuzzy_threshold", 80) or 80)

    if req_sources:
        filtered_df = filtered_df[filtered_df["source"].isin(req_sources)]

    if date_from:
        dt_from = pd.to_datetime(date_from, errors="coerce")
        if pd.notna(dt_from):
            filtered_df = filtered_df[filtered_df["datetime"] >= dt_from]

    if date_to:
        dt_to = pd.to_datetime(date_to, errors="coerce")
        if pd.notna(dt_to):
            dt_to = dt_to + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            filtered_df = filtered_df[filtered_df["datetime"] <= dt_to]

    if req_keywords and not filtered_df.empty:
        combo = (filtered_df["subject"].fillna("") + " " + filtered_df["text"].fillna("")).astype(str)
        mask = combo.apply(
            lambda s: any(_contains_keyword(s, kw, fuzzy_threshold=fuzzy_threshold) for kw in req_keywords)
        )
        filtered_df = filtered_df[mask]

    filtered_df = filtered_df[
        (filtered_df["subject"].str.strip() != "") | (filtered_df["text"].str.strip() != "")
    ]
    return filtered_df.reset_index(drop=True)

def apply_analyze_filters(df: pd.DataFrame, req=None, **kwargs) -> pd.DataFrame:
    return apply_text_filters(df, req, **kwargs)

def _tokenize(text: str, include_numbers=True, include_symbols=True, include_ticket_ids=True) -> List[str]:
    text = _safe_text(text).lower()
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-_']*", text)
    clean = []
    for t in tokens:
        if not include_numbers and any(ch.isdigit() for ch in t):
            continue
        if not include_symbols:
            t = re.sub(r"[^a-z0-9]", "", t)
        if not t:
            continue
        if not include_ticket_ids and re.fullmatch(r"[a-z]+-\d+", t):
            continue
        if t in STOPWORDS or len(t) < 2:
            continue
        clean.append(t)
    return clean

def _extract_phrases(text: str, n: int = 2) -> List[str]:
    tokens = _tokenize(text)
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

def _cluster_messages(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        out["cluster_id"] = []
        return out
    signatures = []
    for _, row in out.iterrows():
        text = f"{_safe_text(row.get('subject'))} {_safe_text(row.get('text'))}"
        phrases = _extract_phrases(text, n=2)
        sig = phrases[0] if phrases else "misc"
        signatures.append(sig)
    unique = {}
    cluster_ids = []
    next_id = 1
    for sig in signatures:
        if sig not in unique:
            unique[sig] = next_id
            next_id += 1
        cluster_ids.append(unique[sig])
    out["cluster_id"] = cluster_ids
    return out

def _build_phrase_groups(top_phrases_df: pd.DataFrame, fuzzy_threshold: int = 80) -> pd.DataFrame:
    if top_phrases_df is None or top_phrases_df.empty:
        return pd.DataFrame(columns=["group_id", "representative", "phrase", "count"])
    phrases = top_phrases_df.to_dict("records")
    groups = []
    used = set()
    gid = 1
    for i, p in enumerate(phrases):
        if i in used:
            continue
        rep = p["phrase"]
        group_members = [p]
        used.add(i)
        for j in range(i + 1, len(phrases)):
            if j in used:
                continue
            q = phrases[j]
            score = int(SequenceMatcher(None, rep, q["phrase"]).ratio() * 100)
            if score >= fuzzy_threshold:
                group_members.append(q)
                used.add(j)
        for m in group_members:
            groups.append({
                "group_id": gid,
                "representative": rep,
                "phrase": m["phrase"],
                "count": int(m["count"]),
            })
        gid += 1
    return pd.DataFrame(groups)

def run_nlp_pipeline(filtered_df: pd.DataFrame, req=None, **kwargs) -> Dict[str, Any]:
    df = _normalize_df(filtered_df)
    
    def get_val(key, default=None):
        if req is not None:
            return getattr(req, key, default)
        return kwargs.get(key, default)

    empty_res = {
        "top_words_df": pd.DataFrame(columns=["word", "count"]),
        "top_phrases_df": pd.DataFrame(columns=["phrase", "count"]),
        "clustered_df": pd.DataFrame(columns=list(df.columns) + ["cluster_id"]),
        "phrase_groups_df": pd.DataFrame(columns=["group_id", "representative", "phrase", "count"]),
        "cluster_counts_df": pd.DataFrame(columns=["cluster_id", "count"]),
    }

    if df.empty:
        return empty_res

    include_numbers = bool(get_val("include_numbers", True))
    include_symbols = bool(get_val("include_symbols", True))
    include_ticket_ids = bool(get_val("include_ticket_ids", True))
    fuzzy_threshold = int(get_val("fuzzy_threshold", 80) or 80)

    corpus = (df["subject"].fillna("") + " " + df["text"].fillna("")).astype(str).tolist()

    word_counter = Counter()
    for text in corpus:
        word_counter.update(_tokenize(text, include_numbers, include_symbols, include_ticket_ids))
    top_words_df = pd.DataFrame(word_counter.most_common(20), columns=["word", "count"])

    phrase_counter = Counter()
    for text in corpus:
        phrase_counter.update(_extract_phrases(text, n=2))
    top_phrases_df = pd.DataFrame(phrase_counter.most_common(15), columns=["phrase", "count"])

    clustered_df = _cluster_messages(df)
    cluster_counts_df = (
        clustered_df.groupby("cluster_id").size()
        .reset_index(name="count")
        .sort_values("count", ascending=False).reset_index(drop=True)
    )

    phrase_groups_df = _build_phrase_groups(top_phrases_df, fuzzy_threshold)

    return {
        "top_words_df": top_words_df,
        "top_phrases_df": top_phrases_df,
        "clustered_df": clustered_df,
        "phrase_groups_df": phrase_groups_df,
        "cluster_counts_df": cluster_counts_df,
    }