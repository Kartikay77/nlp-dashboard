import json
from .security import (
    create_token,
    verify_google_id_token,
    verify_microsoft_access_token,
    get_user_by_email,
)
from .schemas import (
    LoginRequest, 
    AnalyzeRequest, 
    GoogleLoginRequest, 
    MicrosoftLoginRequest,
    JiraIngestRequest,        # Import the simplified version
    OutlookIngestRequest, 
    TeamsIngestRequest,
    PptFolderIngestRequest,
    GmailIngestRequest,
    SharePointPptIngestRequest

)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from .db import Base, engine, get_db
from .schemas import LoginRequest, AnalyzeRequest
from .auth import login_user, get_current_user
from .models import AuditLog
from .services.query_service import load_messages_for_user, apply_business_filters
from .services.nlp_service import apply_text_filters, run_nlp_pipeline
from .services.excel_service import build_excel_dashboard

# Existing ingestion modules
from .ingestion.gmail_ingest import ingest_gmail
from .ingestion.jira_ingest import ingest_jira
from .ingestion.ppt_ingest import ingest_ppt_folder

# New Microsoft Graph ingestion (Outlook / Teams / SharePoint PPT)
# (Make sure backend/app/ingestion/ms_graph_ingest.py exists)
from .ingestion.ms_graph_ingest import (
    ingest_outlook_mail,
    ingest_teams_chats,
    ingest_sharepoint_ppts,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="NLP Access Dashboard API")

# React local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    out = login_user(db, req.username, req.password)
    if not out:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token, user = out
    return {
        "token": token,
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }


# -----------------------------
# Ingestion endpoints
# -----------------------------
@app.post("/ingest/gmail")
def ingest_gmail_api(
    req: GmailIngestRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ingest_gmail(
            owner_role=req.owner_role,
            max_results=req.max_results
        )

        db.add(AuditLog(
            user_email=user["email"],
            action="ingest_gmail",
            filters_used=json.dumps(req.model_dump(exclude={"access_token"}))
        ))
        db.commit()

        return {"status": "ok", "detail": "Gmail ingestion complete", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gmail ingest failed: {str(e)}")


@app.post("/ingest/jira")
def ingest_jira_api(
    req: JiraIngestRequest, # Now uses the simplified schema from schemas.py
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # We no longer pass base_url, email, or api_token here
        # because ingest_jira now fetches them from SourceConfig
        result = ingest_jira(
            jql=req.jql,
            max_results=req.max_results,
            sender_role=req.owner_role # mapped to owner_role in your new schema
        )

        db.add(AuditLog(
            user_email=user["email"],
            action="ingest_jira",
            # Exclude api_token is no longer needed as it's not in the request
            filters_used=json.dumps(req.model_dump())
        ))
        db.commit()

        return {"status": "ok", "detail": "Jira ingestion complete", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Jira ingest failed: {str(e)}")


@app.post("/ingest/ppt-folder")
def ingest_ppt_folder_api(
    req: PptFolderIngestRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ingest_ppt_folder(
            folder_path=req.folder_path,
            owner_role=req.owner_role
        )

        db.add(AuditLog(
            user_email=user["email"],
            action="ingest_ppt_folder",
            filters_used=json.dumps(req.model_dump())
        ))
        db.commit()

        return {"status": "ok", "detail": "Local PPT folder ingestion complete", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PPT folder ingest failed: {str(e)}")


@app.post("/ingest/outlook")
def ingest_outlook_api(
    req: OutlookIngestRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ingest_outlook_mail(
            access_token=req.access_token,
            owner_role=req.owner_role,
            max_results=req.max_results,
            allowed_senders=req.allowed_senders,
        )

        db.add(AuditLog(
            user_email=user["email"],
            action="ingest_outlook",
            filters_used=json.dumps(req.model_dump(exclude={"access_token"}))
        ))
        db.commit()

        return {"status": "ok", "detail": "Outlook ingestion complete", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Outlook ingest failed: {str(e)}")


@app.post("/ingest/teams")
def ingest_teams_api(
    req: TeamsIngestRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ingest_teams_chats(
            access_token=req.access_token,
            owner_role=req.owner_role,
            max_chats=req.max_chats,
            max_messages_per_chat=req.max_messages_per_chat,
        )

        db.add(AuditLog(
            user_email=user["email"],
            action="ingest_teams",
            filters_used=json.dumps(req.model_dump(exclude={"access_token"}))
        ))
        db.commit()

        return {"status": "ok", "detail": "Teams ingestion complete", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Teams ingest failed: {str(e)}")


@app.post("/ingest/sharepoint-ppt")
def ingest_sharepoint_ppt_api(
    req: SharePointPptIngestRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ingest_sharepoint_ppts(
            access_token=req.access_token,
            site_id=req.site_id,
            drive_id=req.drive_id,
            folder_path=req.folder_path,
            owner_role=req.owner_role
        )

        db.add(AuditLog(
            user_email=user["email"],
            action="ingest_sharepoint_ppt",
            filters_used=json.dumps(req.model_dump(exclude={"access_token"}))
        ))
        db.commit()

        return {"status": "ok", "detail": "SharePoint PPT ingestion complete", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SharePoint PPT ingest failed: {str(e)}")


# -----------------------------
# NLP Analyze / Export
# -----------------------------
@app.post("/analyze")
def analyze(req: AnalyzeRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    raw_df = load_messages_for_user(db, user)
    filtered_df = apply_text_filters(raw_df, req=req)
    results = run_nlp_pipeline(filtered_df, req=req)

    db.add(AuditLog(
        user_email=user["email"],
        action="analyze",
        filters_used=json.dumps(req.model_dump())
    ))
    db.commit()

    sample_cols = ["id", "source", "sender", "project_id", "datetime", "subject", "text"]
    if "cluster_id" in results["clustered_df"].columns:
        sample_cols.append("cluster_id")

    sample_messages = (
        results["clustered_df"][sample_cols]
        .head(50)
        .fillna("")
        .to_dict(orient="records")
        if not results["clustered_df"].empty else []
    )

    return {
        "total_raw": int(len(raw_df)),
        "total_filtered": int(len(filtered_df)),
        "top_words": results["top_words_df"].to_dict(orient="records"),
        "top_phrases": results["top_phrases_df"].to_dict(orient="records"),
        "cluster_counts": results["cluster_counts_df"].to_dict(orient="records"),
        "phrase_groups": results["phrase_groups_df"].to_dict(orient="records"),
        "sample_messages": sample_messages
    }


@app.post("/export-excel")
def export_excel(req: AnalyzeRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    raw_df = load_messages_for_user(db, user)
    filtered_df = apply_text_filters(raw_df, req=req)

    results = run_nlp_pipeline(filtered_df, req=req)
    file_path = build_excel_dashboard(raw_df, filtered_df, results)

    db.add(AuditLog(
        user_email=user["email"],
        action="export_excel",
        filters_used=json.dumps(req.model_dump())
    ))
    db.commit()

    return FileResponse(
        file_path,
        filename="nlp_dashboard.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.post("/login/google")
def login_google(payload: GoogleLoginRequest):
    try:
        info = verify_google_id_token(payload.id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    email = (info.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Google account email not available")

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=403, detail="No access configured for this Google account")

    # issue your app token (same token system as username/password login)
    token = create_token({
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "auth_provider": "google"
    })

    return {
        "token": token,
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }


@app.post("/login/microsoft")
def login_microsoft(payload: MicrosoftLoginRequest):
    try:
        info = verify_microsoft_access_token(payload.access_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Microsoft token")

    email = (info.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Microsoft account email not available")

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=403, detail="No access configured for this Microsoft account")

    token = create_token({
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "auth_provider": "microsoft"
    })

    return {
        "token": token,
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }


@app.middleware("http")
async def add_coop_header(request, call_next):
    response = await call_next(request)
    # Allows the popup to stay connected to the parent window
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    return response