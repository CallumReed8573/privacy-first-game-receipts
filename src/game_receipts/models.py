from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class ModerationState(StrEnum):
    QUEUED = "queued"
    APPROVED = "approved"
    REJECTED = "rejected"


class PlayerAsset(BaseModel):
    asset_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1, max_length=80)
    moderation_state: ModerationState


class LiveEvent(BaseModel):
    event_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=100)
    starts_at: datetime


class ReceiptRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    player_email: EmailStr
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    asset: PlayerAsset
    live_event: LiveEvent


class ReceiptResult(BaseModel):
    order_id: str
    delivery: str
    message_id: str | None = None
    reason: str | None = None
