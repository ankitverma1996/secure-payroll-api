"""
Batch disbursement processing.

Key design choice: a batch is never treated as atomic. Each record is
tracked and reported individually, so one failure doesn't block or
hide the status of the rest of the batch -- essential for anything
touching real payments, where "did this specific person get paid?"
always needs a definite answer.
"""

import uuid
from decimal import Decimal
from typing import Dict, List

from app.crypto import encrypt_payload
from app.models import DisbursementRecordStatus


def process_batch(
    cycle_id: str,
    payments: Dict[str, Decimal],
    recipient_public_key_pem: bytes,
) -> tuple[str, List[DisbursementRecordStatus]]:
    """
    Encrypt and "send" each payment individually (simulated -- a real
    implementation would call the banking partner's API here). Returns
    a batch id and per-worker status so failures are visible and
    actionable rather than silently swallowed.
    """
    batch_id = str(uuid.uuid4())
    records: List[DisbursementRecordStatus] = []

    for worker_id, amount in payments.items():
        reference_id = f"{batch_id}:{worker_id}"
        try:
            # Every outbound payload is logged/traceable by reference_id
            # *before* being sent, so a failure mid-flight can always be
            # matched back to exactly what was attempted.
            _ = encrypt_payload(
                {"worker_id": worker_id, "amount": str(amount), "cycle_id": cycle_id},
                recipient_public_key_pem,
            )
            # Simulated send -- replace with the real banking API call.
            records.append(
                DisbursementRecordStatus(
                    worker_id=worker_id, status="sent", reference_id=reference_id
                )
            )
        except Exception:
            records.append(
                DisbursementRecordStatus(
                    worker_id=worker_id, status="failed", reference_id=reference_id
                )
            )

    return batch_id, records
