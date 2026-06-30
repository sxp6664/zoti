"""Idempotent demo seed so the app is usable the moment it boots."""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User, Room, Reservation, Role, RoomStatus


def seed(db: Session):
    if db.query(User).count() > 0:
        return  # already seeded

    # staff users (password = "password" for all, demo only)
    staff = [
        ("manager@zoti.dev", "Maya Manager", Role.manager),
        ("front@zoti.dev", "Riya Reception", Role.receptionist),
        ("clean@zoti.dev", "Hank Housekeeping", Role.housekeeping),
    ]
    for email, name, role in staff:
        db.add(User(email=email, full_name=name,
                    hashed_password=hash_password("password"), role=role))

    # rooms
    rooms = []
    for i in range(1, 13):
        floor = (i - 1) // 4 + 1
        rtype = "suite" if i % 6 == 0 else "deluxe" if i % 2 == 0 else "standard"
        price = {"standard": 99.0, "deluxe": 149.0, "suite": 249.0}[rtype]
        r = Room(number=f"{floor}0{i}", room_type=rtype, floor=floor,
                 price_per_night=price, status=RoomStatus.available)
        rooms.append(r)
        db.add(r)

    # reservations (look these up at the kiosk)
    db.add_all([
        Reservation(confirmation_code="ZOTI-1001", guest_last_name="Patel",
                    guest_full_name="Jordan Patel", nights=2),
        Reservation(confirmation_code="ZOTI-1002", guest_last_name="Nguyen",
                    guest_full_name="Linh Nguyen", nights=1),
        Reservation(confirmation_code="ZOTI-1003", guest_last_name="Garcia",
                    guest_full_name="Diego Garcia", nights=3),
    ])
    db.commit()
