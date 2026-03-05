from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .security import verify_password, create_token, get_user_from_token

bearer_scheme = HTTPBearer(auto_error=False)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def login_user(db: Session, username: str, password: str):
    user = authenticate_user(db, username, password)
    if not user:
        return None
    payload = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }
    token = create_token(payload)
    return token, payload

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    # credentials.scheme should be "Bearer"
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing/invalid Authorization header")

    token = credentials.credentials
    user = get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user