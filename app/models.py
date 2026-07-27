"""
Pydantic models for the Secure Payroll Disbursement API.
"""

from decimal import Decimal
from typing import Dict, List, Literal
from pydantic import BaseModel, Field


class WorkerPay(BaseModel):
    """Gross pay, deductions, and incentives for a single worker."""

    worker_id: str
    gross: Decimal = Field(..., gt=0, description="Gross pay before deductions/incentives")
    deduction: Decimal = Field(default=Decimal("0.00"), ge=0)
    incentive: Decimal = Field(default=Decimal("0.00"), ge=0)


class PayrollComputeRequest(BaseModel):
    """A batch of workers to compute net pay for."""

    cycle_id: str
    workers: List[WorkerPay]


class NetPayResult(BaseModel):
    worker_id: str
    net_pay: Decimal


class PayrollComputeResponse(BaseModel):
    cycle_id: str
    results: List[NetPayResult]


class DisbursementRequest(BaseModel):
    """A batch of confirmed net payments to disburse."""

    cycle_id: str
    payments: Dict[str, Decimal] = Field(
        ..., description="worker_id -> net amount to disburse"
    )


class DisbursementRecordStatus(BaseModel):
    worker_id: str
    status: Literal["queued", "sent", "failed"]
    reference_id: str


class DisbursementResponse(BaseModel):
    cycle_id: str
    batch_id: str
    records: List[DisbursementRecordStatus]
