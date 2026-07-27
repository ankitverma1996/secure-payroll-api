from decimal import Decimal

from app.models import WorkerPay
from app.payroll import compute_net_pay


def test_basic_net_pay():
    workers = [WorkerPay(worker_id="W1", gross=Decimal("50000.00"), deduction=Decimal("2500.50"), incentive=Decimal("1000.00"))]
    results = compute_net_pay(workers)
    assert results[0].net_pay == Decimal("48499.50")


def test_rounding_half_up():
    # 100.005 should round up to 100.01 under ROUND_HALF_UP, not
    # round-to-even (which Python's default `round()` would give).
    workers = [WorkerPay(worker_id="W1", gross=Decimal("100.005"), deduction=Decimal("0"), incentive=Decimal("0"))]
    results = compute_net_pay(workers)
    assert results[0].net_pay == Decimal("100.01")


def test_large_salary_no_precision_loss():
    # Confirms no truncation on larger salaries -- the exact bug we'd be
    # guarding against with a too-low decimal context precision.
    workers = [WorkerPay(worker_id="W1", gross=Decimal("9999999.99"), deduction=Decimal("0"), incentive=Decimal("0"))]
    results = compute_net_pay(workers)
    assert results[0].net_pay == Decimal("9999999.99")


def test_batch_of_multiple_workers():
    workers = [
        WorkerPay(worker_id="W1", gross=Decimal("1000.00")),
        WorkerPay(worker_id="W2", gross=Decimal("2000.00"), deduction=Decimal("500.00")),
    ]
    results = compute_net_pay(workers)
    assert {r.worker_id: r.net_pay for r in results} == {
        "W1": Decimal("1000.00"),
        "W2": Decimal("1500.00"),
    }
