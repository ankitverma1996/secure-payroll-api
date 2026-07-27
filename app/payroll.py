"""
Payroll computation logic.

Uses `decimal.Decimal` throughout (never bare floats) for financial math,
and scopes precision to this module's calls via `localcontext()` rather
than mutating the global decimal context.
"""

from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import List

from app.models import WorkerPay, NetPayResult


def compute_net_pay(workers: List[WorkerPay]) -> List[NetPayResult]:
    """
    Compute net pay for a batch of workers.

    net = gross - deduction + incentive, rounded to 2 decimal places
    (nearest paisa/cent) using ROUND_HALF_UP, which is the conventional
    rounding rule for currency rather than Python's default
    round-half-to-even.
    """
    results: List[NetPayResult] = []

    with localcontext() as ctx:
        ctx.prec = 28  # scoped precision bump; does not leak outside this block

        for worker in workers:
            net = worker.gross - worker.deduction + worker.incentive
            net_rounded = net.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            results.append(NetPayResult(worker_id=worker.worker_id, net_pay=net_rounded))

    return results
