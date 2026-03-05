import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models import ScrapedMessage, AccessScope


EMPTY_COLUMNS = [
    "id", "source", "sender", "sender_role", "project_id",
    "datetime", "subject", "text"
]


def _empty_df():
    return pd.DataFrame(columns=EMPTY_COLUMNS)


def _to_df(rows):
    data = []
    for r in rows:
        data.append({
            "id": r.id,
            "source": r.source,
            "sender": r.sender,
            "sender_role": r.sender_role,
            "project_id": r.project_id,
            "datetime": r.message_datetime,
            "subject": r.subject,
            "text": r.message_text,
        })
    return pd.DataFrame(data)


def fetch_messages_for_user(
    db: Session,
    user: dict,
    source: str | None = None,
    start_date=None,
    end_date=None,
):
    """
    RBAC rules:
    - owner/admin: all messages
    - lead: messages where sender_role='lead' OR sender contains user's email
    - pm: messages in projects assigned in AccessScope
    """
    role = (user.get("role") or "").lower()
    email = (user.get("email") or "").strip().lower()

    q = db.query(ScrapedMessage)

    # Role-based access
    if role in ["owner", "admin"]:
        pass

    elif role == "lead":
        if email:
            q = q.filter(
                or_(
                    ScrapedMessage.sender_role == "lead",
                    ScrapedMessage.sender.ilike(f"%{email}%")
                )
            )
        else:
            q = q.filter(ScrapedMessage.sender_role == "lead")

    elif role == "pm":
        project_ids = [
            x.project_id
            for x in db.query(AccessScope).filter(AccessScope.user_id == user["id"]).all()
            if x.project_id
        ]

        if not project_ids:
            return _empty_df()

        q = q.filter(ScrapedMessage.project_id.in_(project_ids))

    else:
        return _empty_df()

    # Optional DB-level filters
    if source:
        q = q.filter(ScrapedMessage.source == source)

    if start_date:
        q = q.filter(ScrapedMessage.message_datetime >= start_date)

    if end_date:
        q = q.filter(ScrapedMessage.message_datetime <= end_date)

    rows = q.order_by(ScrapedMessage.message_datetime.desc()).all()
    return _to_df(rows)


# ---------------------------------------------------------
# Functions expected by main.py
# ---------------------------------------------------------

def load_messages_for_user(
    db: Session,
    user: dict,
    source: str | None = None,
    start_date=None,
    end_date=None,
):
    """
    Wrapper used by main.py.
    Returns a DataFrame with columns:
    id, source, sender, sender_role, project_id, datetime, subject, text
    """
    return fetch_messages_for_user(
        db=db,
        user=user,
        source=source,
        start_date=start_date,
        end_date=end_date,
    )


def apply_business_filters(
    df: pd.DataFrame,
    sender_roles=None,
    project_ids=None,
    keyword: str | None = None,
):
    """
    Additional in-memory filtering used after RBAC + DB fetch.

    Params:
    - sender_roles: list[str] or None
    - project_ids: list[str] | list[int] or None
    - keyword: substring search across subject + text
    """
    if df is None or df.empty:
        return _empty_df()

    out = df.copy()

    # Filter by sender roles
    if sender_roles:
        sender_roles_set = {str(x).strip().lower() for x in sender_roles if str(x).strip()}
        if sender_roles_set and "sender_role" in out.columns:
            out = out[
                out["sender_role"]
                .astype(str)
                .str.lower()
                .isin(sender_roles_set)
            ]

    # Filter by project IDs
    if project_ids:
        project_ids_set = {str(x).strip() for x in project_ids if str(x).strip()}
        if project_ids_set and "project_id" in out.columns:
            out = out[
                out["project_id"]
                .astype(str)
                .isin(project_ids_set)
            ]

    # Keyword filter across subject + text
    if keyword:
        kw = str(keyword).strip().lower()
        if kw:
            subj = out["subject"].astype(str).str.lower() if "subject" in out.columns else ""
            txt = out["text"].astype(str).str.lower() if "text" in out.columns else ""
            if isinstance(subj, str):  # extremely defensive fallback
                mask = pd.Series([False] * len(out), index=out.index)
            else:
                mask = subj.str.contains(kw, na=False)
                if not isinstance(txt, str):
                    mask = mask | txt.str.contains(kw, na=False)
            out = out[mask]

    # Keep the same ordering/columns shape
    out = out.sort_values(by="datetime", ascending=False, na_position="last")
    return out.reset_index(drop=True)