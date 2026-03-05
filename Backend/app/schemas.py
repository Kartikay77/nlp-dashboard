from pydantic import BaseModel, Field
from typing import List, Optional

# --- AUTH SCHEMAS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    name: str
    email: str
    role: str

class GoogleLoginRequest(BaseModel):
    id_token: str

class MicrosoftLoginRequest(BaseModel):
    access_token: str

# --- NEW INGESTION SCHEMAS (Simplified for DB-access) ---
class JiraIngestRequest(BaseModel):
    """Simplified: Credentials are now pulled from SourceConfig table"""
    jql: str = Field(default="project = 'KAN' ORDER BY created DESC")
    max_results: int = Field(default=50, ge=1, le=100)
    owner_role: str = Field(default="owner")

class OutlookIngestRequest(BaseModel):
    access_token: str # MS tokens are short-lived, so we still pass them via Swagger
    owner_role: str = "owner"
    max_results: int = 50
    allowed_senders: Optional[List[str]] = None

class PptFolderIngestRequest(BaseModel):
    folder_path: str
    owner_role: str = "admin"

class TeamsIngestRequest(BaseModel):
    access_token: str
    owner_role: str = "owner"
    max_chats: int = 10
    max_messages_per_chat: int = 20

# --- ANALYSIS SCHEMAS ---
class AnalyzeRequest(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sources: List[str] = Field(default_factory=list)
    include_numbers: bool = True
    include_symbols: bool = True
    include_ticket_ids: bool = True
    fuzzy_threshold: int = 80

class WordCount(BaseModel):
    word: str
    count: int

class PhraseCount(BaseModel):
    phrase: str
    count: int

class ClusterCount(BaseModel):
    cluster_id: Optional[int]
    count: int

class AnalyzeResponse(BaseModel):
    total_raw: int
    total_filtered: int
    top_words: List[WordCount]
    top_phrases: List[PhraseCount]
    cluster_counts: List[ClusterCount]
    phrase_groups: List[dict]
    sample_messages: List[dict]

class GmailIngestRequest(BaseModel):
    """
    Simplified: Authentication is now handled automatically 
    via Refresh Tokens in the database.
    """
    owner_role: str = Field(default="owner")
    max_results: int = Field(default=50, ge=1, le=500)

class SharePointPptIngestRequest(BaseModel):
    access_token: str
    site_id: str
    drive_id: str
    folder_path: str
    owner_role: str = "owner"
    save_dir: str = "downloads/ppts"