import json
import os
import sqlite3
from datetime import datetime, timezone


def _conn() -> sqlite3.Connection:
    path = os.getenv("DB_PATH", "data/app.db")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS transactions(
              id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT, amount REAL,
              hour INTEGER, new_device INTEGER, new_payee INTEGER, channel TEXT,
              score REAL, level TEXT, reasons TEXT, action TEXT, status TEXT,
              decided_at TEXT);
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY AUTOINCREMENT, tx_id INTEGER, ts TEXT,
              agent TEXT, message TEXT);
            """
        )


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _tx(row) -> dict:
    d = dict(row)
    d["reasons"] = json.loads(d["reasons"])
    d["new_device"], d["new_payee"] = bool(d["new_device"]), bool(d["new_payee"])
    return d


def create_tx(f: dict, score: float, level: str, reasons: list, action: str, status: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO transactions(created_at,amount,hour,new_device,new_payee,channel,"
            "score,level,reasons,action,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (now(), f["amount"], f["hour"], int(f["new_device"]), int(f["new_payee"]),
             f["channel"], score, level, json.dumps(reasons), action, status),
        )
        return cur.lastrowid


def add_event(tx_id: int, agent: str, message: str) -> None:
    with _conn() as c:
        c.execute("INSERT INTO events(tx_id,ts,agent,message) VALUES(?,?,?,?)",
                  (tx_id, now(), agent, message))


def get_tx(tx_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM transactions WHERE id=?", (tx_id,)).fetchone()
        return _tx(row) if row else None


def list_tx(status: str | None = None, limit: int = 50) -> list[dict]:
    q, args = "SELECT * FROM transactions", []
    if status:
        q += " WHERE status=?"
        args.append(status)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with _conn() as c:
        return [_tx(r) for r in c.execute(q, args)]


def set_status(tx_id: int, status: str) -> None:
    with _conn() as c:
        c.execute("UPDATE transactions SET status=?, decided_at=? WHERE id=?",
                  (status, now(), tx_id))


def list_events(limit: int = 50) -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in rows]
