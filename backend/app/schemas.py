"""Request/response schemas."""
from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class RoomOut(BaseModel):
    id: int
    number: str
    room_type: str
    floor: int
    price_per_night: float
    status: str

    class Config:
        from_attributes = True


class ReservationLookup(BaseModel):
    last_name: str
    confirmation_code: str | None = None


class ReservationOut(BaseModel):
    id: int
    confirmation_code: str
    guest_full_name: str
    nights: int
    checked_in: bool
    paid: bool
    room_id: int | None
    key_code: str | None

    class Config:
        from_attributes = True


class SelectRoomIn(BaseModel):
    reservation_id: int
    room_id: int


class PayIn(BaseModel):
    reservation_id: int
