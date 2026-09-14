from __future__ import annotations

from sqlalchemy import text

from Database import engine


def load_booking_kpis() -> dict[str, str]:
    empty = {
        "bookings": "—",
        "commission": "—",
        "platforms": "—",
        "guests": "—",
    }
    try:
        with engine.connect() as conn:
            bookings = conn.execute(text("SELECT COUNT(*) FROM bookings_info")).scalar()
            commission = conn.execute(
                text("SELECT COALESCE(SUM(commission), 0) FROM bookings_info")
            ).scalar()
            platforms = conn.execute(
                text("SELECT COUNT(DISTINCT platform) FROM bookings_info")
            ).scalar()
            guests = conn.execute(
                text("SELECT COUNT(DISTINCT guest_id) FROM bookings_info")
            ).scalar()
        return {
            "bookings": f"{int(bookings or 0):,}",
            "commission": f"{float(commission or 0):,.2f}",
            "platforms": str(int(platforms or 0)),
            "guests": f"{int(guests or 0):,}",
        }
    except Exception:
        return empty
