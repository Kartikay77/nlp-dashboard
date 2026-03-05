import requests
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ScrapedMessage, SourceConfig

def _parse_jira_datetime(dt_str: str):
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)

def _flatten_adf(node):
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    parts = []
    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "text" and "text" in x:
                parts.append(str(x["text"]))
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for item in x:
                walk(item)
    try:
        walk(node)
    except Exception:
        pass 
    return " ".join(parts).strip()

def ingest_jira(jql="ORDER BY updated DESC", max_results=50, sender_role="owner"):
    db = SessionLocal()
    try:
        config = db.query(SourceConfig).filter(SourceConfig.source_name == "jira").first()
        if not config:
            raise Exception("Jira configuration not found in database.")

        base_url = config.base_url
        email = config.email
        api_token = config.api_token

        url = f"{base_url.rstrip('/')}/rest/api/3/search/jql"
        auth = (email, api_token)
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,description,comment,created,updated,assignee,reporter,status,project"
        }
        headers = {"Accept": "application/json"}

        r = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
        if not r.ok:
            raise Exception(f"Jira {r.status_code}: {r.text}")

        data = r.json()
        count, skipped, failed = 0, 0, 0

        for issue in data.get("issues", []):
            try:
                # 1. Extract Unique Jira Key
                issue_key = issue.get("key", "")
                f = issue.get("fields", {}) or {}
                
                summary = (f.get("summary") or "").strip()
                desc_text = _flatten_adf(f.get("description"))
                comment_text = _flatten_adf((f.get("comment") or {}).get("comments", []))
                
                body = "\n".join(x for x in [desc_text, comment_text] if x).strip()
                subject = f"{issue_key}: {summary}" if summary else issue_key

                # 2. Bulletproof Deduplication Check
                # First check by Issue Key (source_message_id)
                exists = db.query(ScrapedMessage).filter(
                    ScrapedMessage.source == "jira",
                    ScrapedMessage.source_message_id == issue_key
                ).first()

                if exists:
                    skipped += 1
                    continue

                # 3. Save with source_message_id
                db.add(ScrapedMessage(
                    source="jira",
                    source_message_id=issue_key, # Store KAN-1 here
                    sender=f.get("reporter", {}).get("displayName", "Jira"),
                    sender_role=sender_role,
                    project_id=f.get("project", {}).get("key"),
                    message_datetime=_parse_jira_datetime(f.get("updated") or f.get("created")),
                    subject=subject,
                    message_text=body or "(no content)",
                ))
                count += 1
            except Exception as e:
                print(f"DEBUG: Failed to process issue {issue.get('key')}: {e}")
                failed += 1
                continue

        db.commit()
        return {"ingested": count, "skipped": skipped, "failed": failed}
    finally:
        db.close()