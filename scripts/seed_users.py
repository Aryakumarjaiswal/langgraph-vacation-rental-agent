"""Add guest or staff users into MySQL registered_users."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)

from Database import SessionLocal
from rag.retriever import property_exists
from services.auth_service import upsert_user


GUESTS = [
    {
        "email": os.getenv("DEMO_GUEST_EMAIL", "guest1@stay.demo"),
        "password": os.getenv("DEMO_GUEST_PASSWORD", "GuestDemo844!"),
        "property_id": os.getenv("DEMO_GUEST_PROPERTY_ID", "910"),
        "full_name": "Demo Guest",
    },
  
    {
        "email": "aryakumarofficial01@gmail.com",
        "password": "aryakumar",
        "property_id": "930",
        "full_name": "Aryan Jaiswal",
    },
]

STAFF = [
    {
        "email": os.getenv("DEMO_STAFF_EMAIL", "staff@stay.demo"),
        "password": os.getenv("DEMO_STAFF_PASSWORD", "StaffDemo#1"),
        "full_name": "Demo Staff",
    },
    {
        "email": "aryakumarofficial02@gmail.com",
        "password": "aryakumar",
        "full_name": "Aryakumar Jaiswal",
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for guest in GUESTS:
            if not property_exists(guest["property_id"]):
                print(
                    f"Warning: no property data for {guest['property_id']}. "
                    "Run the chunk notebook or scripts/rebuild_chroma.py first."
                )
            user = upsert_user(
                db,
                email=guest["email"],
                password=guest["password"],
                role="guest",
                property_id=guest["property_id"],
                full_name=guest["full_name"],
            )
            print(
                f"Guest ready: {user.email} / {guest['password']} "
                f"(property_id in DB = {user.property_id})"
            )

        for member in STAFF:
            staff = upsert_user(
                db,
                email=member["email"],
                password=member["password"],
                role="staff",
                full_name=member["full_name"],
            )
            print(f"Staff ready: {staff.email} / {member['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
