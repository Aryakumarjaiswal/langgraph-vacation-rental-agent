from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from Database import User, hash_password, now_stamp, verify_password


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or user.status != "active":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def upsert_user(
    db: Session,
    email: str,
    password: str,
    role: str,
    property_id: str | None = None,
    full_name: str = "",
) -> User:
    email_norm = email.strip().lower()
    existing = db.query(User).filter(User.email == email_norm).first()
    if existing:
        existing.password_hash = hash_password(password)
        existing.user_role = role
        existing.status = "active"
        existing.property_id = property_id
        existing.full_name = full_name or existing.full_name
        db.commit()
        db.refresh(existing)
        return existing
    user = User(
        user_id=str(uuid.uuid4()),
        email=email_norm,
        password_hash=hash_password(password),
        full_name=full_name,
        user_role=role,
        property_id=property_id,
        status="active",
        created_at=now_stamp(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
