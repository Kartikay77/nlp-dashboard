import base64
import requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from app.db import SessionLocal
from app.models import ScrapedMessage, SourceConfig

def _header(headers, name):
    """Helper to extract a specific header by name."""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return None

def _get_plain_text(payload):
    """Helper to extract plain text from Gmail message payload."""
    parts = [payload]
    while parts:
        part = parts.pop()
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            return base64.urlsafe_b64decode(data).decode("utf-8")
        if "parts" in part:
            parts.extend(part["parts"])
    return None

def _parse_gmail_date(headers):
    """Helper to parse the 'Date' header into a timezone-aware datetime."""
    date_str = _header(headers, "Date")
    if date_str:
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            pass
    return datetime.now(timezone.utc)

def get_gmail_access_token():
    """Fetches a fresh access token from Google using the DB-stored Refresh Token."""
    db = SessionLocal()
    try:
        config = db.query(SourceConfig).filter(SourceConfig.source_name == "gmail").first()
        if not config:
            raise Exception("Gmail configuration not found in database.")

        # REPLACE THIS with your actual Client Secret from Google Cloud Console
        client_secret = "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" 
        
        url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": config.email,      # Your Client ID (stored in 'email' column)
            "client_secret": client_secret,
            "refresh_token": config.api_token, # Your Refresh Token (stored in 'api_token' column)
            "grant_type": "refresh_token"
        }
        
        r = requests.post(url, data=payload)
        if r.ok:
            return r.json().get("access_token")
        else:
            raise Exception(f"Failed to refresh Google token: {r.text}")
    finally:
        db.close()

# ... (_header, _get_plain_text, and _parse_gmail_date helper functions remain the same)

def ingest_gmail(owner_role="owner", max_results=50):
    """
    Automatically refreshes credentials and ingests Gmail messages.
    No longer requires an access_token parameter!
    """
    # 1. Get fresh token automatically
    fresh_token = get_gmail_access_token()
    creds = Credentials(token=fresh_token)
    service = build("gmail", "v1", credentials=creds)

    resp = service.users().messages().list(userId="me", maxResults=max_results).execute()
    msgs = resp.get("messages", [])

    db = SessionLocal()
    count, skipped, failed = 0, 0, 0

    try:
        for m in msgs:
            try:
                msg_id = m["id"] # Permanent Gmail ID
                full = service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()

                payload = full.get("payload", {})
                headers = payload.get("headers", [])

                subject = _header(headers, "Subject") or "(no subject)"
                from_h = _header(headers, "From") or "Unknown"
                body = _get_plain_text(payload) or full.get("snippet", "")
                msg_dt = _parse_gmail_date(headers)

                MAX_LEN = 20000
                safe_body = (body or "").strip()
                if len(safe_body) > MAX_LEN:
                    safe_body = safe_body[:MAX_LEN] + "\n\n...[truncated]"

                # 2. Bulletproof deduplication using source_message_id
                exists = db.query(ScrapedMessage).filter(
                    ScrapedMessage.source == "gmail",
                    ScrapedMessage.source_message_id == msg_id
                ).first()

                if exists:
                    skipped += 1
                    continue

                db.add(ScrapedMessage(
                    source="gmail",
                    source_message_id=msg_id, # Save the permanent ID
                    sender=from_h,
                    sender_role=owner_role,
                    project_id=None,
                    message_datetime=msg_dt,
                    subject=subject,
                    message_text=safe_body,
                ))
                count += 1

            except Exception as e:
                print(f"DEBUG: Failed to process Gmail ID {m.get('id')}: {e}")
                failed += 1
                continue

        db.commit()
    finally:
        db.close()

    return {"ingested": count, "skipped": skipped, "failed": failed}