from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TransactionIn(BaseModel):
    id: str
    user_id: int
    amount: float
    currency: str
    category: Optional[str]
    timestamp: datetime


class StatsResponse(BaseModel):
    total_spent: float
    by_category: dict
    daily_average: float


class UserResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True