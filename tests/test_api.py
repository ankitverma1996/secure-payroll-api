from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _get_token() -> str:
    response = client.post(
        "/token", data={"username": "demo-client", "password": "demo-secret"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_rejects_missing_auth():
    response = client.post("/payroll/compute", json={"cycle_id": "c1", "workers": []})
    assert response.status_code == 401


def test_rejects_bad_credentials():
    response = client.post(
        "/token", data={"username": "demo-client", "password": "wrong"}
    )
    assert response.status_code == 401


def test_compute_and_disburse_flow():
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}"}

    compute_resp = client.post(
        "/payroll/compute",
        headers=headers,
        json={
            "cycle_id": "cycle-1",
            "workers": [
                {"worker_id": "W1", "gross": "50000.00", "deduction": "2500.50", "incentive": "1000.00"}
            ],
        },
    )
    assert compute_resp.status_code == 200
    net_pay = compute_resp.json()["results"][0]["net_pay"]
    assert net_pay == "48499.50"

    disburse_resp = client.post(
        "/payroll/disburse",
        headers=headers,
        json={"cycle_id": "cycle-1", "payments": {"W1": net_pay}},
    )
    assert disburse_resp.status_code == 200
    records = disburse_resp.json()["records"]
    assert records[0]["status"] == "sent"
