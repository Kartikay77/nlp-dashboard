from app.ingestion.ms_graph_ingest import (
    ingest_outlook_mail,
    ingest_teams_chats,
    ingest_sharepoint_ppts,
)

MS_TOKEN = "PASTE_MICROSOFT_GRAPH_ACCESS_TOKEN_HERE"

# 1) Outlook
print(ingest_outlook_mail(
    access_token=MS_TOKEN,
    max_results=50,
    allowed_senders=["lead1@company.com", "owner@company.com"]  # optional
))

# 2) Teams chats
print(ingest_teams_chats(
    access_token=MS_TOKEN,
    max_chats=10,
    max_messages_per_chat=20
))

# 3) SharePoint PPTs
print(ingest_sharepoint_ppts(
    access_token=MS_TOKEN,
    site_id="YOUR_SITE_ID",
    drive_id="YOUR_DRIVE_ID",
    folder_path="Shared Documents/ProjectDecks"
))