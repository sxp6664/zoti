"""The guest self-check-in flow — the heart of Zoti.

Steps a guest takes at the kiosk:
  1. Look up reservation by last name (+ optional confirmation code), OR
     scan an ID document (OCR auto-fills the name to look up).
  2. Select / confirm a room.
  3. Pay (Stripe test mode; mock-completes if no key configured).
  4. Receive a digital key code.

No auth on these endpoints by design — a kiosk guest isn't a logged-in
user. Staff endpoints (rooms admin, dashboards) are separate and RBAC-gated.
"""
import secrets

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models import Reservation, Room, RoomStatus
from app.schemas import (
    ReservationLookup, ReservationOut, SelectRoomIn, PayIn,
)
from app.services.ocr import extract_id_fields

router = APIRouter(prefix="/checkin", tags=["check-in"])


@router.post("/lookup", response_model=ReservationOut)
def lookup(body: ReservationLookup, db: Session = Depends(get_db)):
    q = db.query(Reservation).filter(
        Reservation.guest_last_name.ilike(body.last_name)
    )
    if body.confirmation_code:
        q = q.filter(Reservation.confirmation_code == body.confirmation_code)
    res = q.first()
    if not res:
        raise HTTPException(404, "reservation not found")
    return res


@router.post("/scan-id")
async def scan_id(file: UploadFile = File(...)):
    """OCR an uploaded ID image and return parsed fields for the guest to
    confirm. Returns the extracted last_name the UI then feeds to /lookup."""
    image = await file.read()
    if not image:
        raise HTTPException(400, "empty file")
    fields = extract_id_fields(image)
    return {"extracted": fields}


@router.get("/available-rooms", response_model=list)
def available_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).filter(Room.status == RoomStatus.available).all()
    return [
        {"id": r.id, "number": r.number, "room_type": r.room_type,
         "floor": r.floor, "price_per_night": r.price_per_night}
        for r in rooms
    ]


@router.post("/select-room", response_model=ReservationOut)
def select_room(body: SelectRoomIn, db: Session = Depends(get_db)):
    res = db.get(Reservation, body.reservation_id)
    room = db.get(Room, body.room_id)
    if not res or not room:
        raise HTTPException(404, "reservation or room not found")
    if room.status != RoomStatus.available:
        raise HTTPException(409, "room no longer available")
    res.room_id = room.id
    db.commit()
    db.refresh(res)
    return res


@router.post("/pay", response_model=ReservationOut)
def pay(body: PayIn, db: Session = Depends(get_db)):
    res = db.get(Reservation, body.reservation_id)
    if not res:
        raise HTTPException(404, "reservation not found")
    if not res.room_id:
        raise HTTPException(409, "select a room before paying")

    if settings.STRIPE_ENABLED:
        import stripe  # lazy import; only needed on the real path

        stripe.api_key = settings.STRIPE_SECRET_KEY
        room = db.get(Room, res.room_id)
        amount = int(room.price_per_night * res.nights * 100)  # cents
        # Test-mode PaymentIntent; front end would confirm with Stripe.js.
        intent = stripe.PaymentIntent.create(
            amount=amount, currency="usd",
            metadata={"reservation": res.confirmation_code},
        )
        res.paid = True  # demo simplification; real flow confirms via webhook
        db.commit()
        db.refresh(res)
        return res

    # mock payment (no Stripe key configured)
    res.paid = True
    db.commit()
    db.refresh(res)
    return res


@router.post("/complete", response_model=ReservationOut)
def complete(body: PayIn, db: Session = Depends(get_db)):
    """Finalize check-in: mark occupied, issue digital key."""
    res = db.get(Reservation, body.reservation_id)
    if not res:
        raise HTTPException(404, "reservation not found")
    if not res.paid:
        raise HTTPException(402, "payment required")
    room = db.get(Room, res.room_id)
    room.status = RoomStatus.occupied
    res.checked_in = True
    res.key_code = secrets.token_hex(4).upper()  # digital room credential
    db.commit()
    db.refresh(res)
    return res
