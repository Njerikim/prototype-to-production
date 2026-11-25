from . import agents, db
from .models import TransactionIn

_model: agents.RiskModel = agents.RuleRiskModel()


def run(tx: TransactionIn) -> dict:
    """Intake -> Risk -> Action -> Human. Every step is written to the audit log."""
    features, intake_msg = agents.intake(tx)
    score, reasons = _model.score(features)
    lvl = agents.level(score)
    action = agents.decide(score)
    status, human_msg = agents.human_status(action)

    risk_msg = f"Risk {score:.2f}: {lvl}" + (f" ({', '.join(reasons)})" if reasons else "")
    action_msg = {"approve": "Approve the payment",
                  "hold": "Hold it and ask the owner",
                  "block": "Block it and alert the owner"}[action]
    steps = [("Intake", intake_msg), ("Risk", risk_msg),
             ("Action", action_msg), ("Human", human_msg)]

    tx_id = db.create_tx(features, score, lvl, reasons, action, status)
    for agent, msg in steps:
        db.add_event(tx_id, agent, msg)
    return {"id": tx_id, "score": score, "level": lvl, "reasons": reasons,
            "action": action, "status": status,
            "steps": [{"agent": a, "message": m} for a, m in steps]}


def decide(tx_id: int, decision: str) -> dict | None:
    """Owner resolves a held payment. Returns None if it is not pending."""
    tx = db.get_tx(tx_id)
    if tx is None or tx["status"] != "pending":
        return None
    status = "approved" if decision == "approve" else "declined"
    db.set_status(tx_id, status)
    db.add_event(tx_id, "Human", f"Owner {status} the payment. Logged for audit.")
    return db.get_tx(tx_id)
