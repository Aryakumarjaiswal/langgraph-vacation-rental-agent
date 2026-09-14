from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from Database import SessionLocal, User
from services.auth_service import authenticate
from services.executive_service import handoff_twiml

app = FastAPI(title="StayOps API", version="2.1.0")
router = APIRouter(prefix="/api/v1")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)


def user_payload(user: User) -> dict:
    return {
        "id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "user_role": {"role": user.user_role},
        "property_id": user.property_id,
        "status": user.status,
    }


@router.post("/auth/login")
def login(payload: LoginRequest, db: DbSession):
    """Local login. Property access comes from registered_users.property_id."""
    user = authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"user": user_payload(user)}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/twilio/handoff")
@app.post("/twilio/handoff")
def twilio_handoff(property_id: str = "", reason: str = "support request"):
    """TwiML spoken to support when they answer the outbound call."""
    return Response(
        content=handoff_twiml(property_id, reason),
        media_type="application/xml",
    )


app.include_router(router)
