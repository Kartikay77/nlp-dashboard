from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    username = Column(String(80), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # lead, pm, owner, admin
    is_active = Column(Boolean, default=True)


class AccessScope(Base):
    __tablename__ = "access_scope"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(String(50), nullable=False)

    user = relationship("User", backref="scopes")


class ScrapedMessage(Base):
    __tablename__ = "scraped_messages"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(30), nullable=False)  # gmail/outlook/teams/jira/ppt
    sender = Column(String(200), nullable=False)
    sender_role = Column(String(50), nullable=True)
    project_id = Column(String(50), nullable=True)
    message_datetime = Column(DateTime, default=datetime.utcnow)
    subject = Column(String(300), nullable=True)
    message_text = Column(Text, nullable=False)
    
    # New fields for NLP Clustering and Deduplication
    cluster_id = Column(Integer, nullable=True)
    source_message_id = Column(String(255), unique=True, nullable=True) 


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(200), nullable=False)
    action = Column(String(100), nullable=False)
    filters_used = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# New Table for storing API Credentials
class SourceConfig(Base):
    __tablename__ = "source_configs"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(50), unique=True, nullable=False) # e.g. 'jira'
    api_token = Column(Text, nullable=False)
    email = Column(String(255), nullable=False)
    base_url = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)