import bcrypt
import secrets
from typing import Dict, Optional
import requests  # NEW

# Simple in-memory token store for MVP.
# In production use JWT + expiry.
TOKEN_STORE: Dict[str, dict] = {}

# OPTIONAL: in-memory user directory for OAuth mapping (MVP)
# Replace with DB lookup later
OAUTH_USER_MAP = {
        "erkg1111@gmail.com": {
        "name": "Kartikay Gupta",
        "email": "erkg1111@gmail.com",
        "role": "owner"
    },
    "kartikaygupta2026@hotmail.com": {
        "name": "Kartikay Gupta",
        "email": "kartikaygupta2026@hotmail.com",
        "role": "admin"
    }
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_payload: dict) -> str:
    token = secrets.token_urlsafe(32)
    TOKEN_STORE[token] = user_payload
    return token


def get_user_from_token(token: str) -> Optional[dict]:
    return TOKEN_STORE.get(token)


# ---------------------------
# NEW: OAuth helper functions
# ---------------------------

def get_user_by_email(email: str) -> Optional[dict]:
    """MVP email lookup for OAuth login. Replace with DB query later."""
    if not email:
        return None
    return OAUTH_USER_MAP.get(email.lower().strip())


def verify_google_id_token(id_token: str) -> dict:
    """
    Verifies Google ID token using tokeninfo endpoint (MVP-friendly).
    Returns dict with email/name/provider/sub.
    """
    resp = requests.get(
        "https://oauth2.googleapis.com/tokeninfo",
        params={"id_token": id_token},
        timeout=10,
    )
    if resp.status_code != 200:
        raise ValueError("Invalid Google token")

    data = resp.json()
    # Optional hardening: validate data["aud"] == YOUR_GOOGLE_CLIENT_ID

    return {
        "email": data.get("email"),
        "name": data.get("name") or data.get("given_name") or "Google User",
        "provider": "google",
        "sub": data.get("sub"),
    }


def verify_microsoft_access_token(access_token: str) -> dict:
    """
    Verifies Microsoft access token by calling Graph /me.
    Returns dict with email/name/provider/sub.
    """
    resp = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise ValueError("Invalid Microsoft token")

    data = resp.json()
    email = data.get("mail") or data.get("userPrincipalName")
    name = data.get("displayName") or "Microsoft User"

    return {
        "email": email,
        "name": name,
        "provider": "microsoft",
        "sub": data.get("id"),
    }