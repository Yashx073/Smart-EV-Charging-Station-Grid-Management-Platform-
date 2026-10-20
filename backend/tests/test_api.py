import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from bson import ObjectId

from app.security import hash_password, verify_password


def utc(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
def test_password_hashing():
    h = hash_password("Secret123!")
    assert h != "Secret123!"
    assert verify_password("Secret123!", h)
    assert not verify_password("Wrong", h)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
async def register(client, email, password="CustomerPass123!", role=None):
    payload = {
        "email": email,
        "password": password,
        "full_name": "Test User",
    }
    return await client.post("/api/auth/register", json=payload)


async def login(client, email, password="CustomerPass123!"):
    return await client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )


async def auth_headers(client, email, password="CustomerPass123!"):
    await register(client, email, password)  # idempotent-ish within a clean DB
    r = await login(client, email, password)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ---------------------------------------------------------------------------
# Registration / login
# ---------------------------------------------------------------------------
async def test_register_and_login(client):
    r = await register(client, "alice@example.com")
    assert r.status_code == 201, r.text
    r = await login(client, "alice@example.com")
    assert r.status_code == 200
    assert "access_token" in r.json()
    me = await client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"
    assert me.json()["role"] == "customer"


async def test_duplicate_email_rejection(client):
    await register(client, "bob@example.com")
    r = await register(client, "bob@example.com")
    assert r.status_code == 409, r.text


async def test_login_wrong_password(client):
    await register(client, "carol@example.com")
    r = await login(client, "carol@example.com", "WrongPass")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# CRUD (EVs)
# ---------------------------------------------------------------------------
async def test_ev_crud_customer(client):
    token = await auth_headers(client, "dave@example.com")
    ev = {
        "model": "Tesla Model 3",
        "registration_number": "EV-001",
        "battery_capacity_kwh": 75.0,
        "connector_type": "CCS",
    }
    r = await client.post("/api/evs", json=ev)
    assert r.status_code == 201, r.text
    ev_id = r.json()["id"]

    r = await client.get("/api/evs")
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = await client.put(f"/api/evs/{ev_id}", json={"model": "Tesla Model Y"})
    assert r.status_code == 200
    assert r.json()["model"] == "Tesla Model Y"

    # customer cannot delete (admin only)
    r = await client.delete(f"/api/evs/{ev_id}")
    assert r.status_code == 403


async def test_invalid_objectid(client):
    await auth_headers(client, "eve@example.com")
    r = await client.get("/api/evs/not-an-objectid")
    assert r.status_code == 400, r.text


# ---------------------------------------------------------------------------
# Role-based authorization
# ---------------------------------------------------------------------------
async def test_customer_cannot_access_admin_endpoints(client):
    await auth_headers(client, "frank@example.com")
    r = await client.get("/api/admin/users")
    assert r.status_code == 403, r.text


async def test_admin_access(client):
    # register then promote via direct DB insert for the test
    from app.database import get_db
    from app.security import hash_password
    from datetime import datetime, timezone

    db = await get_db()
    await db["users"].insert_one(
        {
            "email": "admin@example.com",
            "password_hash": hash_password("AdminPass123!"),
            "full_name": "Admin",
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
    )
    r = await login(client, "admin@example.com", "AdminPass123!")
    assert r.status_code == 200
    r = await client.get("/api/admin/users")
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Booking: creation, overlap, validation, cancellation
# ---------------------------------------------------------------------------
async def _seed_port_and_ev(client, db):
    # admin-owned station/port/ev via direct DB insert, owned by customer user
    await auth_headers(client, "grace@example.com")
    me = (await client.get("/api/auth/me")).json()
    user_id = me["id"]
    now = datetime.now(timezone.utc)
    station = {
        "name": "T Station",
        "station_code": "TST-1",
        "address": "1 Main St",
        "city": "C",
        "latitude": 0.0,
        "longitude": 0.0,
        "status": "operational",
        "created_at": now,
    }
    sr = await db["charging_stations"].insert_one(station)
    station_id = str(sr.inserted_id)
    pr = await db["charging_ports"].insert_one(
        {
            "station_id": station_id,
            "port_number": 1,
            "connector_type": "CCS",
            "rated_power_kw": 50.0,
            "status": "operational",
            "created_at": now,
        }
    )
    port_id = str(pr.inserted_id)
    er = await db["evs"].insert_one(
        {
            "owner_id": user_id,
            "model": "Leaf",
            "registration_number": "LEAF-1",
            "battery_capacity_kwh": 40.0,
            "connector_type": "CCS",
            "is_active": True,
            "created_at": now,
        }
    )
    ev_id = str(er.inserted_id)
    return user_id, station_id, port_id, ev_id


async def test_booking_create_and_overlap(client):
    from app.database import get_db

    db = await get_db()
    user_id, station_id, port_id, ev_id = await _seed_port_and_ev(client, db)
    start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=1, hours=2)).isoformat()

    r = await client.post(
        "/api/bookings",
        json={
            "ev_id": ev_id,
            "station_id": station_id,
            "port_id": port_id,
            "start_time": start,
            "end_time": end,
        },
    )
    assert r.status_code == 201, r.text
    booking_id = r.json()["id"]

    # Overlapping booking -> reject
    r2 = await client.post(
        "/api/bookings",
        json={
            "ev_id": ev_id,
            "station_id": station_id,
            "port_id": port_id,
            "start_time": (datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat(),
            "end_time": (datetime.now(timezone.utc) + timedelta(days=1, hours=3)).isoformat(),
        },
    )
    assert r2.status_code == 400, r2.text

    # Past start time -> reject
    r3 = await client.post(
        "/api/bookings",
        json={
            "ev_id": ev_id,
            "station_id": station_id,
            "port_id": port_id,
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "end_time": (datetime.now(timezone.utc)).isoformat(),
        },
    )
    assert r3.status_code == 400, r3.text

    # Cancel
    r4 = await client.post(f"/api/bookings/{booking_id}/cancel")
    assert r4.status_code == 200, r4.text
    assert r4.json()["status"] == "cancelled"

    # Cannot cancel again
    r5 = await client.post(f"/api/bookings/{booking_id}/cancel")
    assert r5.status_code == 400, r5.text


async def test_concurrent_booking(client):
    from app.database import get_db

    db = await get_db()
    user_id, station_id, port_id, ev_id = await _seed_port_and_ev(client, db)
    start = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    end = (datetime.now(timezone.utc) + timedelta(days=2, hours=1)).isoformat()

    payload = {
        "ev_id": ev_id,
        "station_id": station_id,
        "port_id": port_id,
        "start_time": start,
        "end_time": end,
    }

    async def book(c):
        return await c.post("/api/bookings", json=payload)

    results = await asyncio.gather(book(client), book(client))
    statuses = sorted([r.status_code for r in results])
    assert statuses == [201, 400], statuses


# ---------------------------------------------------------------------------
# Session + billing
# ---------------------------------------------------------------------------
async def test_session_billing_20kwh_is_240(client):
    from app.database import get_db

    db = await get_db()
    user_id, station_id, port_id, ev_id = await _seed_port_and_ev(client, db)
    # confirmed booking
    b = await db["bookings"].insert_one(
        {
            "user_id": user_id,
            "ev_id": ev_id,
            "station_id": station_id,
            "port_id": port_id,
            "start_time": datetime.now(timezone.utc) + timedelta(days=1),
            "end_time": datetime.now(timezone.utc) + timedelta(days=1, hours=2),
            "status": "confirmed",
            "created_at": datetime.now(timezone.utc),
        }
    )
    booking_id = str(b.inserted_id)

    # tariff ₹12/kWh
    await db["tariffs"].insert_one(
        {
            "name": "Test Tariff",
            "price_per_kwh": 12.0,
            "valid_from": datetime.now(timezone.utc) - timedelta(days=1),
            "valid_to": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
    )

    r = await client.post(
        "/api/sessions/start",
        json={"booking_id": booking_id, "port_id": port_id},
    )
    assert r.status_code == 201, r.text
    session_id = r.json()["id"]

    r = await client.post(
        f"/api/sessions/{session_id}/end",
        json={"energy_delivered_kwh": 20},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_amount"] == 240.0, body
    assert body["tariff_price_per_kwh"] == 12.0
    assert body["energy_delivered_kwh"] == 20.0

    # duplicate billing prevention: end again -> 400
    r2 = await client.post(
        f"/api/sessions/{session_id}/end",
        json={"energy_delivered_kwh": 5},
    )
    assert r2.status_code == 400, r2.text

    # one active session per port: start another on same port -> 400
    r3 = await client.post(
        "/api/sessions/start",
        json={"booking_id": booking_id, "port_id": port_id},
    )
    assert r3.status_code == 400, r3.text


async def test_customer_data_isolation(client):
    from app.database import get_db

    db = await get_db()
    now = datetime.now(timezone.utc)
    await db["charging_stations"].insert_one(
        {
            "name": "S", "station_code": "ISO-1", "address": "a", "city": "c",
            "latitude": 0.0, "longitude": 0.0, "status": "operational", "created_at": now,
        }
    )
    await db["charging_ports"].insert_one(
        {"station_id": "iso-station", "port_number": 1, "connector_type": "CCS",
         "rated_power_kw": 50.0, "status": "operational", "created_at": now}
    )

    # register two customers
    await register(client, "iso1@example.com")
    me1 = (await client.get("/api/auth/me")).json()  # cookie is iso1 now; capture id
    # re-login to get fresh cookie, but keep me1 id
    await login(client, "iso1@example.com")
    id1 = me1["id"]

    await register(client, "iso2@example.com")
    me2 = (await client.get("/api/auth/me")).json()
    id2 = me2["id"]

    await db["bookings"].insert_one(
        {"user_id": id1, "ev_id": "e1", "station_id": "iso-station", "port_id": "p1",
         "start_time": now + timedelta(days=1), "end_time": now + timedelta(days=1, hours=1),
         "status": "confirmed", "created_at": now}
    )
    await db["bookings"].insert_one(
        {"user_id": id2, "ev_id": "e2", "station_id": "iso-station", "port_id": "p1",
         "start_time": now + timedelta(days=2), "end_time": now + timedelta(days=2, hours=1),
         "status": "confirmed", "created_at": now}
    )

    # log in as user1
    await login(client, "iso1@example.com")
    r = await client.get("/api/bookings")
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(b["user_id"] == id1 for b in items)
    assert len(items) == 1


# ---------------------------------------------------------------------------
# Maintenance (admin)
# ---------------------------------------------------------------------------
async def test_maintenance_crud_admin(client):
    from app.database import get_db
    from app.security import hash_password
    from datetime import datetime, timezone

    db = await get_db()
    db["users"].insert_one(
        {
            "email": "maintadmin@example.com",
            "password_hash": hash_password("AdminPass123!"),
            "full_name": "Maint Admin",
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
    )
    await login(client, "maintadmin@example.com", "AdminPass123!")

    r = await client.post(
        "/api/maintenance",
        json={
            "title": "Cable check",
            "description": "Inspect cables",
            "status": "planned",
        },
    )
    assert r.status_code == 201, r.text
    mid = r.json()["id"]
    r = await client.get("/api/maintenance")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    r = await client.put(f"/api/maintenance/{mid}", json={"status": "completed"})
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
async def test_dashboard_stats(client):
    await auth_headers(client, "dash@example.com")
    r = await client.get("/api/dashboard/stats")
    assert r.status_code == 200, r.text
    body = r.json()
    for k in ["total_users", "total_stations", "total_ports", "total_bookings",
              "total_sessions", "total_revenue", "total_maintenance"]:
        assert k in body


async def test_dashboard_trends(client):
    await auth_headers(client, "dash2@example.com")
    r = await client.get("/api/dashboard/trends?days=7")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "booking_trend" in body
    assert "revenue_trend" in body
    assert "energy_trend" in body


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
async def test_logout(client):
    await auth_headers(client, "logout@example.com")
    r = await client.post("/api/auth/logout")
    assert r.status_code == 200
    me = await client.get("/api/auth/me")
    assert me.status_code == 401
