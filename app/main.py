"""
Secure Payroll Disbursement API.

A small, self-contained demo of patterns used in production payroll
systems: async FastAPI endpoints, Pydantic validation, OAuth2
client-credentials auth, Decimal-correct financial math, and hybrid
AES/RSA encryption with per-record batch tracking for disbursement.

Run locally:
    uvicorn app.main:app --reload

Then visit http://localhost:8000/docs for interactive API docs.
"""

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import issue_token, verify_token
from app.crypto import generate_demo_keypair
from app.disbursement import process_batch
from app.models import (
    DisbursementRequest,
    DisbursementResponse,
    PayrollComputeRequest,
    PayrollComputeResponse,
)
from app.payroll import compute_net_pay

app = FastAPI(
    title="Secure Payroll Disbursement API",
    description="Demo microservice: payroll computation + encrypted batch disbursement.",
    version="1.0.0",
)

# Demo keypair generated at startup so the service is runnable standalone.
# In production these would be loaded from a secrets manager, never generated
# fresh on each boot.
_DEMO_PRIVATE_KEY, _DEMO_PUBLIC_KEY = generate_demo_keypair()


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 client-credentials-style token endpoint (demo)."""
    token = issue_token(form_data.username, form_data.password)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/payroll/compute", response_model=PayrollComputeResponse)
def compute_payroll(
    request: PayrollComputeRequest, token: str = Depends(verify_token)
) -> PayrollComputeResponse:
    """Compute net pay for a batch of workers."""
    results = compute_net_pay(request.workers)
    return PayrollComputeResponse(cycle_id=request.cycle_id, results=results)


@app.post("/payroll/disburse", response_model=DisbursementResponse)
def disburse_payroll(
    request: DisbursementRequest, token: str = Depends(verify_token)
) -> DisbursementResponse:
    """Encrypt and disburse a confirmed batch of net payments."""
    batch_id, records = process_batch(
        request.cycle_id, request.payments, _DEMO_PUBLIC_KEY
    )
    return DisbursementResponse(
        cycle_id=request.cycle_id, batch_id=batch_id, records=records
    )


@app.get("/health")
def health():
    return {"status": "ok"}
