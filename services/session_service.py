from datetime import datetime

from Database import Chat, ChatTransfer, SessionLocal, Session_Table, now_stamp


def start_session(user_id: str, user_type: str) -> str:
    db = SessionLocal()
    try:
        session = Session_Table(
            user_id=str(user_id),
            user_type=user_type,
            status="active",
            started_at=now_stamp(),
            ended_at=now_stamp(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session.session_id
    finally:
        db.close()


def append_chat(session_id: str, user_text: str, bot_text: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(Session_Table).filter_by(session_id=session_id).first()
        if not user:
            return
        stamp = now_stamp()
        blob = f"\n USER-> {user_text}\n RESPONSE-> {bot_text}"
        record = db.query(Chat).filter_by(session_id=session_id).first()
        if not record:
            db.add(
                Chat(
                    session_id=session_id,
                    sender="user",
                    message=blob,
                    sent_at=stamp,
                    status="read",
                )
            )
        else:
            record.message = (record.message or "") + blob
            record.sent_at = stamp
        user.ended_at = stamp
        if user.started_at:
            ended = datetime.strptime(user.ended_at, "%Y-%m-%d %H:%M")
            started = datetime.strptime(user.started_at, "%Y-%m-%d %H:%M")
            user.Duration = str((ended - started).total_seconds())
        db.commit()
    finally:
        db.close()


def log_transfer(session_id: str, reason: str) -> None:
    db = SessionLocal()
    try:
        db.add(
            ChatTransfer(
                session_id=session_id,
                transferred_by="bot",
                transfer_reason=reason,
                transferred_at=now_stamp(),
            )
        )
        session = db.query(Session_Table).filter_by(session_id=session_id).first()
        if session:
            session.status = "transferred"
            session.ended_at = now_stamp()
        db.commit()
    finally:
        db.close()
