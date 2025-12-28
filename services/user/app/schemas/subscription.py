from uuid import UUID
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.db.models import PlanInterval, SubscriptionStatus


class PlanBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    price: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    interval: PlanInterval = Field(default=PlanInterval.MONTHLY)
    max_devices: int = Field(default=1, ge=1)
    supports_hd: bool = False
    supports_4k: bool = False


class PlanResponse(PlanBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionBase(BaseModel):
    plan_id: UUID
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    start_date: datetime
    payment_reference: str | None = None


class SubscriptionResponse(BaseModel):
    id: UUID
    profile_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    start_date: datetime
    end_date: datetime | None
    cancelled_at: datetime | None
    auto_renew: bool
    created_at: datetime
    updated_at: datetime

    plan: PlanResponse | None = None

    model_config = {"from_attributes": True}
