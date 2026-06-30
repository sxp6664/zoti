"""Data model for the self-check-in flow.

Roles use a simple enum on the user. RBAC is enforced in `core/security.py`
via a dependency that checks the JWT's role claim against the route's
required roles.
"""
import enum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Role(str, enum.Enum):
    guest = "guest"
    receptionist = "receptionist"
    housekeeping = "housekeeping"
    manager = "manager"


class RoomStatus(str, enum.Enum):
    available = "available"
    occupied = "occupied"
    cleaning = "cleaning"
    out_of_service = "out_of_service"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.guest)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    number = Column(String, unique=True, nullable=False, index=True)
    room_type = Column(String, nullable=False)        # standard, deluxe, suite
    floor = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.available, index=True)


class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True)
    confirmation_code = Column(String, unique=True, index=True, nullable=False)
    guest_last_name = Column(String, index=True, nullable=False)
    guest_full_name = Column(String, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    nights = Column(Integer, default=1)
    checked_in = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    key_code = Column(String, nullable=True)          # digital room credential
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("Room")
