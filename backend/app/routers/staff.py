"""Staff-facing endpoints, RBAC-gated.

Demonstrates two things interviewers ask about:
  - role-based access control (require_roles dependency)
  - Redis caching with explicit invalidation on writes
"""
import json

import redis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import require_roles
from app.models import Reservation, Room, RoomStatus, Role

router = APIRouter(tags=["staff"])
cache = redis.from_url(settings.REDIS_URL, decode_responses=True)
ROOMS_KEY = "rooms:all"


# ---------- Rooms (cached read) ----------
@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    """Cache-aside: serve from Redis if warm, else read Postgres and
    backfill the cache with a short TTL."""
    cached = cache.get(ROOMS_KEY)
    if cached:
        return {"source": "cache", "rooms": json.loads(cached)}
    rooms = db.query(Room).all()
    payload = [
        {"id": r.id, "number": r.number, "type": r.room_type,
         "floor": r.floor, "price": r.price_per_night, "status": r.status.value}
        for r in rooms
    ]
    cache.setex(ROOMS_KEY, settings.ROOM_CACHE_TTL, json.dumps(payload))
    return {"source": "db", "rooms": payload}


# ---------- Housekeeping ----------
@router.post("/housekeeping/{room_id}/clean")
def mark_clean(
    room_id: int,
    db: Session = Depends(get_db),
    _claims=Depends(require_roles(Role.housekeeping, Role.manager)),
):
    room = db.get(Room, room_id)
    room.status = RoomStatus.available
    db.commit()
    cache.delete(ROOMS_KEY)  # invalidate on write
    return {"room": room.number, "status": room.status.value}


# ---------- Manager analytics ----------
@router.get("/analytics/summary")
def analytics(
    db: Session = Depends(get_db),
    _claims=Depends(require_roles(Role.manager)),
):
    total = db.query(Room).count()
    occupied = db.query(Room).filter(Room.status == RoomStatus.occupied).count()
    checked_in = db.query(Reservation).filter(Reservation.checked_in.is_(True)).count()
    revenue = (
        db.query(Room.price_per_night)
        .join(Reservation, Reservation.room_id == Room.id)
        .filter(Reservation.paid.is_(True))
        .all()
    )
    return {
        "total_rooms": total,
        "occupied": occupied,
        "occupancy_rate": round(occupied / total, 3) if total else 0,
        "guests_checked_in": checked_in,
        "revenue_collected": round(sum(p[0] for p in revenue), 2),
    }
