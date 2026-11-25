import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db, pipeline
from .models import DecisionIn, TransactionIn


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init()
    yield


def require_key(x_api_key: str | None = Header(default=None)) -> None:
    """If API_KEY is set, every API call must send it as X-API-Key."""
    key = os.getenv("API_KEY")
    if key and x_api_key != key:
        raise HTTPException(401, "Invalid or missing API key")


app = FastAPI(title="From Prototype to Production", lifespan=lifespan)
auth = [Depends(require_key)]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/transactions", status_code=201, dependencies=auth)
def create_transaction(tx: TransactionIn):
    return pipeline.run(tx)


@app.get("/transactions", dependencies=auth)
def list_transactions(status: str | None = None, limit: int = 50):
    return db.list_tx(status, min(limit, 200))


@app.get("/transactions/{tx_id}", dependencies=auth)
def get_transaction(tx_id: int):
    tx = db.get_tx(tx_id)
    if tx is None:
        raise HTTPException(404, "Transaction not found")
    return tx


@app.post("/transactions/{tx_id}/decision", dependencies=auth)
def decide(tx_id: int, body: DecisionIn):
    result = pipeline.decide(tx_id, body.decision)
    if result is None:
        raise HTTPException(409, "Transaction is not pending")
    return result


@app.get("/audit", dependencies=auth)
def audit(limit: int = 50):
    return db.list_events(min(limit, 200))


@app.get("/")
def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
