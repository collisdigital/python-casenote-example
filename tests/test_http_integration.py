"""Integration tests exercising the full HTTP routing stack.

These hit the real FastAPI app and the real SQLAlchemy repository, but against
an in-memory SQLite database (wired via a dependency override in conftest).
This verifies the inbound adapter, IoC wiring, service, and outbound adapter
all collaborate correctly end to end.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_full_crud_lifecycle(client: AsyncClient) -> None:
    # Create
    create_resp = await client.post(
        "/case-notes",
        json={
            "hospital_number": "RX1234567",
            "current_location": "Medical Records Library",
        },
    )
    assert create_resp.status_code == 201
    body = create_resp.json()
    tracking_id = body["tracking_id"]
    assert body["current_location"] == "Medical Records Library"
    assert body["status"] == "FILED"

    # List
    list_resp = await client.get("/case-notes")
    assert list_resp.status_code == 200
    assert any(item["tracking_id"] == tracking_id for item in list_resp.json())

    # Move
    move_resp = await client.patch(
        f"/case-notes/{tracking_id}/location",
        json={"current_location": "Ward 4", "status": "ON_LOAN"},
    )
    assert move_resp.status_code == 200
    assert move_resp.json()["current_location"] == "Ward 4"
    assert move_resp.json()["status"] == "ON_LOAN"

    # Delete
    delete_resp = await client.delete(f"/case-notes/{tracking_id}")
    assert delete_resp.status_code == 204

    # Confirm gone
    get_resp = await client.get(f"/case-notes/{tracking_id}")
    assert get_resp.status_code == 404


async def test_invalid_hospital_number_returns_422(client: AsyncClient) -> None:
    resp = await client.post(
        "/case-notes",
        json={"hospital_number": "bad", "current_location": "Ward 4"},
    )
    assert resp.status_code == 422


async def test_get_unknown_returns_404(client: AsyncClient) -> None:
    resp = await client.get(f"/case-notes/{uuid.uuid4()}")
    assert resp.status_code == 404
