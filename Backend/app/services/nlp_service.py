# import re
# from collections import Counter
# from difflib import SequenceMatcher
# from typing import List, Dict, Any

# import pandas as pd

# STOPWORDS = {
#     "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with", "is", "are",
#     "was", "were", "be", "been", "being", "this", "that", "it", "as", "at", "by", "from",
#     "but", "not", "no", "yes", "we", "you", "they", "he", "she", "i", "me", "my", "our",
#     "your", "their", "them", "us", "can", "could", "should", "would", "will", "just",
#     "have", "has", "had", "do", "does", "did", "if", "then", "than", "so", "such",
# }

# def _safe_text(x) -> str:
#     if x is None:
#         return ""
#     return str(x)

# def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
#     if df is None or df.empty:
#         return pd.DataFrame(columns=["id", "source", "sender", "sender_role", "project_id", "datetime", "subject", "text"])

#     out = df.copy()
#     for col in ["id", "source", "sender", "sender_role", "project_id", "datetime", "subject", "text"]:
#         if col not in out.columns:
#             out[col] = None

#     out["source"] = out["source"].fillna("").astype(str).str.lower().str.strip()
#     out["sender"] = out["sender"].fillna("").astype(str)
#     out["sender_role"] = out["sender_role"].fillna("").astype(str)
#     out["project_id"] = out["project_id"].fillna("").astype(str)
#     out["subject"] = out["subject"].fillna("").astype(str)
#     out["text"] = out["text"].fillna("").astype(str)
#     out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce")
#     return out

# def _contains_keyword(text: str, keyword: str, fuzzy_threshold: int = 80) -> bool:
#     text = _safe_text(text).lower()
#     kw = _safe_text(keyword).lower().strip()
#     if not kw:
#         return False
#     if kw in text:
#         return True
#     words = text.split()
#     kw_words = kw.split()
#     win = max(1, len(kw_words))
#     for i in range(0, max(1, len(words) - win + 1)):
#         chunk = " ".join(words[i:i + win])
#         ratio = int(SequenceMatcher(None, chunk, kw).ratio() * 100)
#         if ratio >= fuzzy_threshold:
#             return True
#     return False

# def apply_text_filters(df: pd.DataFrame, req=None, **kwargs) -> pd.DataFrame:
#     """
#     Fixed to handle both Pydantic 'req' objects and direct keyword arguments.
#     """
#     filtered_df = _normalize_df(df)
#     if filtered_df.empty:
#         return filtered_df

#     # Helper to pull from req object OR kwargs
#     def get_val(key, default=None):
#         if req is not None:
#             return getattr(req, key, default)
#         return kwargs.get(key, default)

#     req_sources = [str(s).strip().lower() for s in (get_val("sources", []) or []) if str(s).strip()]
#     req_keywords = [str(k).strip() for k in (get_val("keywords", []) or []) if str(k).strip()]
#     date_from = get_val("date_from")
#     date_to = get_val("date_to")
#     fuzzy_threshold = int(get_val("fuzzy_threshold", 80) or 80)

#     if req_sources:
#         filtered_df = filtered_df[filtered_df["source"].isin(req_sources)]

#     if date_from:
#         dt_from = pd.to_datetime(date_from, errors="coerce")
#         if pd.notna(dt_from):
#             filtered_df = filtered_df[filtered_df["datetime"] >= dt_from]

#     if date_to:
#         dt_to = pd.to_datetime(date_to, errors="coerce")
#         if pd.notna(dt_to):
#             dt_to = dt_to + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
#             filtered_df = filtered_df[filtered_df["datetime"] <= dt_to]

#     if req_keywords and not filtered_df.empty:
#         combo = (filtered_df["subject"].fillna("") + " " + filtered_df["text"].fillna("")).astype(str)
#         mask = combo.apply(
#             lambda s: any(_contains_keyword(s, kw, fuzzy_threshold=fuzzy_threshold) for kw in req_keywords)
#         )
#         filtered_df = filtered_df[mask]

#     filtered_df = filtered_df[
#         (filtered_df["subject"].str.strip() != "") | (filtered_df["text"].str.strip() != "")
#     ]
#     return filtered_df.reset_index(drop=True)

# def apply_analyze_filters(df: pd.DataFrame, req=None, **kwargs) -> pd.DataFrame:
#     return apply_text_filters(df, req, **kwargs)

# def _tokenize(text: str, include_numbers=True, include_symbols=True, include_ticket_ids=True) -> List[str]:
#     text = _safe_text(text).lower()
#     tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-_']*", text)
#     clean = []
#     for t in tokens:
#         if not include_numbers and any(ch.isdigit() for ch in t):
#             continue
#         if not include_symbols:
#             t = re.sub(r"[^a-z0-9]", "", t)
#         if not t:
#             continue
#         if not include_ticket_ids and re.fullmatch(r"[a-z]+-\d+", t):
#             continue
#         if t in STOPWORDS or len(t) < 2:
#             continue
#         clean.append(t)
#     return clean

# def _extract_phrases(text: str, n: int = 2) -> List[str]:
#     tokens = _tokenize(text)
#     if len(tokens) < n:
#         return []
#     return [" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]

# def _cluster_messages(df: pd.DataFrame) -> pd.DataFrame:
#     out = df.copy()
#     if out.empty:
#         out["cluster_id"] = []
#         return out
#     signatures = []
#     for _, row in out.iterrows():
#         text = f"{_safe_text(row.get('subject'))} {_safe_text(row.get('text'))}"
#         phrases = _extract_phrases(text, n=2)
#         sig = phrases[0] if phrases else "misc"
#         signatures.append(sig)
#     unique = {}
#     cluster_ids = []
#     next_id = 1
#     for sig in signatures:
#         if sig not in unique:
#             unique[sig] = next_id
#             next_id += 1
#         cluster_ids.append(unique[sig])
#     out["cluster_id"] = cluster_ids
#     return out

# def _build_phrase_groups(top_phrases_df: pd.DataFrame, fuzzy_threshold: int = 80) -> pd.DataFrame:
#     if top_phrases_df is None or top_phrases_df.empty:
#         return pd.DataFrame(columns=["group_id", "representative", "phrase", "count"])
#     phrases = top_phrases_df.to_dict("records")
#     groups = []
#     used = set()
#     gid = 1
#     for i, p in enumerate(phrases):
#         if i in used:
#             continue
#         rep = p["phrase"]
#         group_members = [p]
#         used.add(i)
#         for j in range(i + 1, len(phrases)):
#             if j in used:
#                 continue
#             q = phrases[j]
#             score = int(SequenceMatcher(None, rep, q["phrase"]).ratio() * 100)
#             if score >= fuzzy_threshold:
#                 group_members.append(q)
#                 used.add(j)
#         for m in group_members:
#             groups.append({
#                 "group_id": gid,
#                 "representative": rep,
#                 "phrase": m["phrase"],
#                 "count": int(m["count"]),
#             })
#         gid += 1
#     return pd.DataFrame(groups)

# def run_nlp_pipeline(filtered_df: pd.DataFrame, req=None, **kwargs) -> Dict[str, Any]:
#     df = _normalize_df(filtered_df)
    
#     def get_val(key, default=None):
#         if req is not None:
#             return getattr(req, key, default)
#         return kwargs.get(key, default)

#     empty_res = {
#         "top_words_df": pd.DataFrame(columns=["word", "count"]),
#         "top_phrases_df": pd.DataFrame(columns=["phrase", "count"]),
#         "clustered_df": pd.DataFrame(columns=list(df.columns) + ["cluster_id"]),
#         "phrase_groups_df": pd.DataFrame(columns=["group_id", "representative", "phrase", "count"]),
#         "cluster_counts_df": pd.DataFrame(columns=["cluster_id", "count"]),
#     }

#     if df.empty:
#         return empty_res

#     include_numbers = bool(get_val("include_numbers", True))
#     include_symbols = bool(get_val("include_symbols", True))
#     include_ticket_ids = bool(get_val("include_ticket_ids", True))
#     fuzzy_threshold = int(get_val("fuzzy_threshold", 80) or 80)

#     corpus = (df["subject"].fillna("") + " " + df["text"].fillna("")).astype(str).tolist()

#     word_counter = Counter()
#     for text in corpus:
#         word_counter.update(_tokenize(text, include_numbers, include_symbols, include_ticket_ids))
#     top_words_df = pd.DataFrame(word_counter.most_common(20), columns=["word", "count"])

#     phrase_counter = Counter()
#     for text in corpus:
#         phrase_counter.update(_extract_phrases(text, n=2))
#     top_phrases_df = pd.DataFrame(phrase_counter.most_common(15), columns=["phrase", "count"])

#     clustered_df = _cluster_messages(df)
#     cluster_counts_df = (
#         clustered_df.groupby("cluster_id").size()
#         .reset_index(name="count")
#         .sort_values("count", ascending=False).reset_index(drop=True)
#     )

#     phrase_groups_df = _build_phrase_groups(top_phrases_df, fuzzy_threshold)

#     return {
#         "top_words_df": top_words_df,
#         "top_phrases_df": top_phrases_df,
#         "clustered_df": clustered_df,
#         "phrase_groups_df": phrase_groups_df,
#         "cluster_counts_df": cluster_counts_df,
#     }
import re
from collections import Counter
from difflib import SequenceMatcher
from typing import List, Dict, Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

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
    filtered_df = _normalize_df(df)
    if filtered_df.empty:
        return filtered_df

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

def _choose_k(n_rows: int) -> int:
    if n_rows <= 2:
        return 1
    if n_rows <= 5:
        return 2
    if n_rows <= 12:
        return 3
    if n_rows <= 25:
        return 4
    if n_rows <= 50:
        return 5
    if n_rows <= 100:
        return 6
    return 8

def _cluster_messages(df: pd.DataFrame, n_clusters: int = None) -> pd.DataFrame:
    out = df.copy()

    if out.empty:
        out["cluster_id"] = pd.Series(dtype="int64")
        out["cluster_label"] = pd.Series(dtype="object")
        return out

    corpus = (
        out["subject"].fillna("").astype(str).str.strip() + " " +
        out["text"].fillna("").astype(str).str.strip()
    ).str.strip()

    non_empty_mask = corpus.str.len() > 0
    if non_empty_mask.sum() == 0:
        out["cluster_id"] = 1
        out["cluster_label"] = "misc"
        return out

    valid_idx = out.index[non_empty_mask]
    valid_corpus = corpus.loc[valid_idx].tolist()

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=1000,
        min_df=1
    )
    X = vectorizer.fit_transform(valid_corpus)

    if X.shape[0] == 1:
        out["cluster_id"] = 1
        out["cluster_label"] = "single_message"
        return out

    k = n_clusters if n_clusters is not None else _choose_k(X.shape[0])
    k = max(1, min(k, X.shape[0]))

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)

    feature_names = vectorizer.get_feature_names_out()
    order_centroids = km.cluster_centers_.argsort(axis=1)[:, ::-1]

    cluster_name_map = {}
    for cluster_num in range(k):
        top_terms = []
        for idx in order_centroids[cluster_num][:3]:
            term = feature_names[idx].strip()
            if term:
                top_terms.append(term)
        label_text = ", ".join(top_terms) if top_terms else f"cluster_{cluster_num + 1}"
        cluster_name_map[cluster_num] = label_text

    out["cluster_id"] = -1
    out["cluster_label"] = "misc"

    for row_idx, cluster_num in zip(valid_idx, labels):
        out.at[row_idx, "cluster_id"] = int(cluster_num) + 1
        out.at[row_idx, "cluster_label"] = cluster_name_map[int(cluster_num)]

    if (out["cluster_id"] == -1).any():
        fallback_cluster = k + 1
        out.loc[out["cluster_id"] == -1, "cluster_id"] = fallback_cluster
        out.loc[out["cluster_id"] == -1, "cluster_label"] = "misc"

    out["cluster_id"] = out["cluster_id"].astype(int)
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
        "clustered_df": pd.DataFrame(columns=list(df.columns) + ["cluster_id", "cluster_label"]),
        "phrase_groups_df": pd.DataFrame(columns=["group_id", "representative", "phrase", "count"]),
        "cluster_counts_df": pd.DataFrame(columns=["cluster_id", "cluster_label", "count"]),
    }

    if df.empty:
        return empty_res

    include_numbers = bool(get_val("include_numbers", True))
    include_symbols = bool(get_val("include_symbols", True))
    include_ticket_ids = bool(get_val("include_ticket_ids", True))
    fuzzy_threshold = int(get_val("fuzzy_threshold", 80) or 80)
    requested_k = get_val("n_clusters")

    corpus = (df["subject"].fillna("") + " " + df["text"].fillna("")).astype(str).tolist()

    word_counter = Counter()
    for text in corpus:
        word_counter.update(_tokenize(text, include_numbers, include_symbols, include_ticket_ids))
    top_words_df = pd.DataFrame(word_counter.most_common(20), columns=["word", "count"])

    phrase_counter = Counter()
    for text in corpus:
        phrase_counter.update(_extract_phrases(text, n=2))
    top_phrases_df = pd.DataFrame(phrase_counter.most_common(15), columns=["phrase", "count"])

    clustered_df = _cluster_messages(df, n_clusters=requested_k)

    cluster_counts_df = (
        clustered_df.groupby(["cluster_id", "cluster_label"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "cluster_id"], ascending=[False, True])
        .reset_index(drop=True)
    )

    phrase_groups_df = _build_phrase_groups(top_phrases_df, fuzzy_threshold)

    return {
        "top_words_df": top_words_df,
        "top_phrases_df": top_phrases_df,
        "clustered_df": clustered_df,
        "phrase_groups_df": phrase_groups_df,
        "cluster_counts_df": cluster_counts_df,
    }
