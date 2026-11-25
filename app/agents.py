"""The four agents. Each one has a single job and returns plain data."""
import os
from typing import Protocol

from .models import TransactionIn

HOLD_AT = float(os.getenv("RISK_HOLD", "0.3"))
BLOCK_AT = float(os.getenv("RISK_BLOCK", "0.7"))


def intake(tx: TransactionIn) -> tuple[dict, str]:
    """Agent 1: normalise a raw payment into features the risk agent can use."""
    features = {
        "amount": tx.amount,
        "hour": tx.hour,
        "new_device": tx.new_device,
        "new_payee": tx.new_payee,
        "channel": tx.channel,
    }
    msg = (
        f"KES {tx.amount:,.0f} at {tx.hour}:00 via {tx.channel}, "
        f"{'new' if tx.new_device else 'known'} device, "
        f"{'first-time' if tx.new_payee else 'known'} payee"
    )
    return features, msg


class RiskModel(Protocol):
    def score(self, features: dict) -> tuple[float, list[str]]: ...


class RuleRiskModel:
    """Transparent baseline. Swap in an online-learning model (e.g. River)
    by implementing the same `score` method."""

    def score(self, f: dict) -> tuple[float, list[str]]:
        s, why = 0.02, []
        if f["amount"] > 50_000:
            s += 0.35
            why.append("amount above KES 50,000")
        elif f["amount"] > 10_000:
            s += 0.15
            why.append("amount above KES 10,000")
        if f["hour"] < 5 or f["hour"] > 22:
            s += 0.20
            why.append("unusual hour")
        if f["new_device"]:
            s += 0.25
            why.append("new device")
        if f["new_payee"]:
            s += 0.15
            why.append("first-time payee")
        return round(min(s, 0.99), 2), why


def level(score: float) -> str:
    return "low" if score < HOLD_AT else "medium" if score < BLOCK_AT else "high"


def decide(score: float) -> str:
    """Agent 3: turn a score into an action."""
    return "approve" if score < HOLD_AT else "hold" if score < BLOCK_AT else "block"


def human_status(action: str) -> tuple[str, str]:
    """Agent 4: the human step. Returns (status, message)."""
    if action == "approve":
        return "approved", "Not needed. Logged for audit."
    if action == "hold":
        return "pending", "Owner is asked to confirm. Logged for audit."
    return "blocked", "Owner is alerted. Logged for audit."
