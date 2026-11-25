from typing import Literal
from pydantic import BaseModel, Field


class TransactionIn(BaseModel):
    amount: float = Field(gt=0, description="Amount in KES")
    hour: int = Field(ge=0, le=23, description="Hour of day, 0 to 23")
    new_device: bool = False
    new_payee: bool = False
    channel: Literal["mpesa", "pos", "invoice"] = "mpesa"


class DecisionIn(BaseModel):
    decision: Literal["approve", "decline"]
