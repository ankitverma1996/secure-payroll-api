# Secure Payroll Disbursement API

A small, self-contained FastAPI microservice demonstrating patterns used
in production payroll and banking-disbursement systems: async APIs,
OAuth2 client-credentials auth, decimal-correct financial math, and
hybrid AES/RSA encryption for outbound payment payloads.

This is a portfolio project built to demonstrate architecture and
implementation patterns — it is not connected to any real bank or
production data.

## Why these design choices

**Decimal, not float, for money.** `app/payroll.py` uses `decimal.Decimal`
throughout and rounds with `ROUND_HALF_UP` (the conventional rounding
rule for currency), rather than Python's default round-half-to-even.
Precision is scoped per-call via `localcontext()` instead of mutating
the global decimal context, so this module can't silently affect
unrelated calculations elsewhere in a larger service.

**Hybrid encryption, not raw RSA.** `app/crypto.py` generates a fresh
AES-256 key per request, encrypts the actual payload with AES-CBC, and
only RSA-encrypts the small AES key. RSA alone can't encrypt arbitrary-
length payloads and is far slower than AES for bulk data — this is the
standard pattern for encrypting variable-size payloads for a recipient
who only holds an RSA keypair.

**Batches are never atomic.** `app/disbursement.py` tracks and reports
success/failure per record. A production system moving real money
should never let one bad record silently block or hide the status of
the rest of a batch — every worker's payment needs a definite,
individually-traceable outcome.

**OAuth2 client-credentials, not static API keys.** `app/auth.py`
implements the shape of a real client-credentials flow: short-lived,
scoped bearer tokens instead of a long-lived static secret sent on
every request.

## Project structure

```
app/
  main.py          # FastAPI app + routes
  models.py        # Pydantic request/response models
  payroll.py        # Net pay computation (Decimal-correct)
  crypto.py         # Hybrid AES/RSA encryption
  disbursement.py    # Batch processing with per-record status
  auth.py           # OAuth2 client-credentials auth (demo)
tests/
  test_payroll.py
  test_crypto.py
  test_api.py
```

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs for interactive Swagger docs.

**Get a token:**
```bash
curl -X POST http://localhost:8000/token \
  -d "username=demo-client&password=demo-secret"
```

**Compute payroll:**
```bash
curl -X POST http://localhost:8000/payroll/compute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "cycle_id": "cycle-1",
    "workers": [
      {"worker_id": "W1", "gross": "50000.00", "deduction": "2500.50", "incentive": "1000.00"}
    ]
  }'
```

## Running tests

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t secure-payroll-api .
docker run -p 8000:8000 secure-payroll-api
```

## What I'd add for a real production version

- Real identity provider integration (Azure AD/MSAL) instead of the
  in-memory demo token store
- Persistent storage (Postgres/Dataverse) instead of in-memory state
- A reconciliation job comparing "sent" records against the banking
  partner's actual settlement confirmations, since a real disbursement
  flow is asynchronous — this demo simulates the send but not the
  async callback step
- Structured logging and retry logic with capped attempts on the
  disbursement path
