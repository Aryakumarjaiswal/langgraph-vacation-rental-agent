"""MySQL models — core tables only."""

import uuid
from datetime import datetime
from pathlib import Path
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import bcrypt

load_dotenv()

db_user = os.getenv("DB_USER", "root").strip()
db_password = (os.getenv("DB_PASSWORD") or "").strip().strip('"').strip("'")
db_host = os.getenv("DB_HOST", "localhost").strip()
db_port = os.getenv("DB_PORT", "3306").strip()
db_name = os.getenv("DB_NAME", "Conversations").strip()

if not db_password:
    raise RuntimeError("DB_PASSWORD is missing in .env")

DATABASE_URL = (
    f"mysql+pymysql://{db_user}:{quote_plus(db_password)}"
    f"@{db_host}:{db_port}/{db_name}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


class User(Base):
    __tablename__ = "registered_users"

    user_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=False, default="guest")
    property_id = Column(String(50), nullable=True)
    status = Column(
        Enum("pending_payment", "active", "disabled"),
        nullable=False,
        default="active",
    )
    created_at = Column(String(50), nullable=True)


class Session_Table(Base):
    __tablename__ = "Session_table_2"

    session_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    user_id = Column(String(50))
    user_type = Column(String(50), nullable=False, default="user")
    status = Column(
        Enum("active", "closed", "transferred"), nullable=False, default="active"
    )
    started_at = Column(String(50), nullable=True)
    ended_at = Column(String(50), nullable=True)
    Duration = Column(String(50), nullable=True)
    chats = relationship("Chat", back_populates="session")
    chat_transfers = relationship("ChatTransfer", back_populates="session")


class Chat(Base):
    __tablename__ = "Chat_table"

    chat_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(225), ForeignKey("Session_table_2.session_id"))
    sender = Column(Enum("user", "bot", "agent"), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(String(50), nullable=True)
    status = Column(Enum("unread", "read"), default="read")
    session = relationship("Session_Table", back_populates="chats")


class ChatTransfer(Base):
    __tablename__ = "chat_transfer_table"

    transfer_id = Column(
        CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    session_id = Column(String(225), ForeignKey("Session_table_2.session_id"))
    transferred_by = Column(String(50))
    transfer_reason = Column(Text, nullable=True)
    transferred_at = Column(String(50), nullable=True)
    agent_id = Column(CHAR(36), default=lambda: str(uuid.uuid4()), index=True)
    session = relationship("Session_Table", back_populates="chat_transfers")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def now_stamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M")


init_db()
