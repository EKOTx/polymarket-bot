"""Public-facing form schemas (waitlist, contact)."""

from pydantic import BaseModel, EmailStr


class WaitlistRequest(BaseModel):
    email: EmailStr
    marketing_consent: bool = False


class WaitlistResponse(BaseModel):
    message: str
    already_registered: bool = False


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str


class ContactResponse(BaseModel):
    message: str
