# From Prototype to Production

A small multi-agent payment-screening backend, built as the companion to the talk
**"From Prototype to Production: Building Autonomous Multi-Agent Systems for Africa's Fintech Ecosystem"**
(Tambua Women in Tech Summit Kenya, 27 to 28 November 2026).

Each incoming payment passes through four agents, and every step is written to an audit log:

1. **Intake** reads and normalises the payment (M-Pesa, POS or invoice).
2. **Risk** scores it and explains why.
3. **Action** approves, holds or blocks it.
4. **Human** lets the owner confirm held payments and is alerted on blocked ones.

> The risk model is a transparent set of rules on synthetic data. It is a baseline to
> show the architecture, not a production fraud model. See "Swap in a real model" below.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the demo page, or http://localhost:8000/docs for the API docs.

With Docker:

```bash
docker build -t p2p . && docker run -p 8000:8000 p2p
```

## API

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/transactions` | Run a payment through the four agents |
| GET | `/transactions?status=pending` | List payments, optionally by status |
| GET | `/transactions/{id}` | One payment |
| POST | `/transactions/{id}/decision` | Owner approves or declines a held payment |
| GET | `/audit` | Latest audit events |
| GET | `/health` | Health check |

Example:

```bash
curl -X POST localhost:8000/transactions -H 'Content-Type: application/json' \
  -d '{"amount": 85000, "hour": 2, "new_device": true}'
```

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `DB_PATH` | `data/app.db` | SQLite file |
| `API_KEY` | unset | If set, send it as the `X-API-Key` header on every API call |
| `RISK_HOLD` | `0.3` | Scores at or above this are held for the owner |
| `RISK_BLOCK` | `0.7` | Scores at or above this are blocked |

If you set `API_KEY`, the demo page will not work, because it does not send the key.

## Tests

```bash
pytest
```

## Swap in a real model

`app/agents.py` defines a `RiskModel` protocol with one method, `score(features)`. Implement it
with an online-learning model (for example [River](https://riverml.xyz)) and assign it to
`_model` in `app/pipeline.py`. Nothing else changes.

## Layout

```
app/        agents, pipeline, SQLite storage, FastAPI routes
static/     demo page
tests/      API tests
```
