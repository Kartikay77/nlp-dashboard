from datetime import datetime, timedelta
from app.db import Base, engine, SessionLocal
from app.models import User, AccessScope, ScrapedMessage
from app.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# reset demo data
db.query(AccessScope).delete()
db.query(ScrapedMessage).delete()
db.query(User).delete()
db.commit()

users = [
    User(
        name="Lead One",
        email="lead1@company.com",
        username="lead1",
        password_hash=hash_password("pass123"),
        role="lead",
        is_active=True
    ),
    User(
        name="PM One",
        email="pm1@company.com",
        username="pm1",
        password_hash=hash_password("pass123"),
        role="pm",
        is_active=True
    ),
    User(
        name="Owner One",
        email="owner@company.com",
        username="owner",
        password_hash=hash_password("pass123"),
        role="owner",
        is_active=True
    ),
    User(
        name="Admin One",
        email="admin@company.com",
        username="admin",
        password_hash=hash_password("pass123"),
        role="admin",
        is_active=True
    ),
]
db.add_all(users)
db.commit()

pm_user = db.query(User).filter(User.username == "pm1").first()
db.add_all([
    AccessScope(user_id=pm_user.id, project_id="PROJ-A"),
    AccessScope(user_id=pm_user.id, project_id="PROJ-B"),
])
db.commit()

base_time = datetime.now()

demo_msgs = [
    ("gmail","lead1@company.com","lead","PROJ-A","Timeline update","Need ETA for release 2.1 by Friday. Blocked by API dependency."),
    ("teams","dev1@company.com","engineer","PROJ-A","", "Blocked on API integration. Need timeline update and owner response."),
    ("outlook","pm1@company.com","pm","PROJ-A","Risk review","Risk: vendor delay 3 days. Please share updated ETA and mitigation."),
    ("jira","qa@company.com","qa","PROJ-A","BUG-1024","BUG-1024 still pending. Repro on build 241. Urgent fix needed."),
    ("ppt","ppt_document","document","PROJ-B","Weekly_Review.pptx","Slide mentions timeline slip, budget risk, and dependency issue."),
    ("gmail","owner@company.com","owner","PROJ-B","Escalation","Escalation: customer issue pending. Need follow up and action items."),
    ("teams","lead2@company.com","lead","PROJ-C","", "Please send numbers for sprint velocity: 21, 18, 24 and defect trend."),
    ("outlook","manager@company.com","lead","PROJ-B","Budget","Budget variance is 12%. Need explanation and recovery plan."),
    ("jira","pm1@company.com","pm","PROJ-B","PROJ-221","PROJ-221 dependency issue. Waiting on external vendor."),
    ("gmail","analyst@company.com","analyst","PROJ-C","Status","Status green. No blockers today."),
]

rows = []
for i, (src, sender, srole, proj, subj, txt) in enumerate(demo_msgs):
    rows.append(ScrapedMessage(
        source=src,
        sender=sender,
        sender_role=srole,
        project_id=proj,
        message_datetime=base_time - timedelta(days=i),
        subject=subj,
        message_text=txt
    ))

db.add_all(rows)
db.commit()
db.close()

print("Seeded demo data.")
print("Demo logins:")
print("lead1 / pass123")
print("pm1   / pass123")
print("owner / pass123")
print("admin / pass123")