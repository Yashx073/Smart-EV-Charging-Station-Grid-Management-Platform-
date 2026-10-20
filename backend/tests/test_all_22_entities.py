import asyncio
from datetime import datetime, timedelta, timezone
import pytest
from bson import ObjectId

from app.database import (
    ALL_COLLECTIONS,
    USERS,
    ADMINS,
    get_db,
)
from app.security import hash_password


async def create_admin_and_login(client, email="superadmin@example.com", password="AdminPass123!"):
    db = await get_db()
    await db[USERS].delete_many({"email": email})
    now = datetime.now(timezone.utc)
    res = await db[USERS].insert_one({
        "email": email,
        "password_hash": hash_password(password),
        "full_name": "Super Admin",
        "role": "admin",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    })
    await db[ADMINS].update_one(
        {"email": email},
        {"$set": {
            "user_id": str(res.inserted_id),
            "email": email,
            "admin_name": "Super Admin",
            "role": "SUPER_ADMIN",
            "experience": 10,
            "privileges": ["manage_users", "manage_stations", "manage_tariffs"],
            "created_at": now,
        }},
        upsert=True,
    )
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def create_customer_and_login(client, email="cust1@example.com", password="CustPass123!"):
    db = await get_db()
    await db[USERS].delete_many({"email": email})
    r = await client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test Customer",
        "phone": "+1-555-9999",
    })
    assert r.status_code == 201, r.text
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# ---------------------------------------------------------------------------
# Test 1: Verify all 22 collections are registered
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_all_22_collections_defined():
    assert len(ALL_COLLECTIONS) == 22
    expected = {
        "users", "admins", "tariffs", "sources", "charging_stations", "evs",
        "user_phones", "grids", "charging_ports", "ac_ports", "dc_fast_ports",
        "bookings", "charging_sessions", "payments", "schedules", "maintenance",
        "notifications", "battery_status", "renewable_sources",
        "non_renewable_sources", "preventive_maintenance", "corrective_maintenance",
    }
    assert set(ALL_COLLECTIONS) == expected


# ---------------------------------------------------------------------------
# Test 2: Users & User Phones CRUD & Composite Unique Index
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_users_and_phones_crud(client):
    admin_token = await create_admin_and_login(client, "admin_user_phone@example.com")

    # Create User via /api/users
    u_res = await client.post("/api/users", json={
        "email": "user_with_phones@example.com",
        "password": "Password123!",
        "full_name": "John MultiPhone",
        "first_name": "John",
        "last_name": "MultiPhone",
        "phone": "+1-555-0101",
        "address": "123 Elm St",
        "date_of_birth": "1990-05-15",
    })
    assert u_res.status_code == 201, u_res.text
    u_data = u_res.json()
    user_id = u_data["id"]

    # Read User
    get_res = await client.get(f"/api/users/{user_id}")
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "user_with_phones@example.com"
    assert get_res.json()["address"] == "123 Elm St"

    # Add Phone 1
    p1 = await client.post("/api/user-phones", json={
        "user_id": user_id,
        "number": "+1-555-1111",
        "label": "Mobile",
        "is_primary": True,
    })
    assert p1.status_code == 201, p1.text

    # Add Phone 2
    p2 = await client.post("/api/user-phones", json={
        "user_id": user_id,
        "number": "+1-555-2222",
        "label": "Work",
        "is_primary": False,
    })
    assert p2.status_code == 201, p2.text

    # Duplicate phone for same user must be rejected
    dup_p = await client.post("/api/user-phones", json={
        "user_id": user_id,
        "number": "+1-555-1111",
        "label": "Mobile",
    })
    assert dup_p.status_code == 400

    # List phones for user
    plist = await client.get(f"/api/user-phones?user_id={user_id}")
    assert plist.status_code == 200
    assert plist.json()["total"] == 2


# ---------------------------------------------------------------------------
# Test 3: Admin Entity CRUD (/api/admins)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_admins_crud(client):
    admin_token = await create_admin_and_login(client, "admin_runner@example.com")

    # Create secondary admin
    adm_res = await client.post("/api/admins", json={
        "email": "ops_lead@example.com",
        "admin_name": "Operations Lead",
        "phone_no": "+1-555-4321",
        "role": "OPERATIONS",
        "experience": 7,
        "password": "OpsPassword123!",
    })
    assert adm_res.status_code == 201, adm_res.text
    adm_id = adm_res.json()["id"]

    # Get admin
    get_adm = await client.get(f"/api/admins/{adm_id}")
    assert get_adm.status_code == 200
    assert get_adm.json()["experience"] == 7
    assert get_adm.json()["role"] == "OPERATIONS"

    # Update admin
    upd_adm = await client.put(f"/api/admins/{adm_id}", json={"experience": 8})
    assert upd_adm.status_code == 200
    assert upd_adm.json()["experience"] == 8

    # List admins
    list_adm = await client.get("/api/admins")
    assert list_adm.status_code == 200
    assert list_adm.json()["total"] >= 2


# ---------------------------------------------------------------------------
# Test 4: Energy Sources & Subtypes (Renewable / Non-Renewable)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sources_and_subtypes(client):
    admin_token = await create_admin_and_login(client, "admin_sources@example.com")

    # 1. Create parent SOURCE
    src_res = await client.post("/api/sources", json={
        "name": "Green Valley Solar Farm",
        "source_type": "RENEWABLE",
        "capacity_kw": 2400.0,
        "status": "ACTIVE",
        "description": "Photovoltaic solar generation plant",
    })
    assert src_res.status_code == 201, src_res.text
    source_id = src_res.json()["id"]

    # 2. Create RENEWABLE_SOURCE subtype linked to parent
    ren_res = await client.post("/api/renewable-sources", json={
        "source_id": source_id,
        "renewable_type": "SOLAR",
        "generation_efficiency": 23.5,
        "capacity_kw": 2400.0,
        "name": "Green Valley Solar Farm",
    })
    assert ren_res.status_code == 201, ren_res.text
    assert ren_res.json()["renewable_type"] == "SOLAR"

    # 3. Create non-renewable parent and subtype
    gas_src = await client.post("/api/sources", json={
        "name": "Reserve Turbine Gamma",
        "source_type": "NON_RENEWABLE",
        "capacity_kw": 5000.0,
        "status": "ACTIVE",
    })
    assert gas_src.status_code == 201, gas_src.text
    gas_source_id = gas_src.json()["id"]

    non_ren = await client.post("/api/non-renewable-sources", json={
        "source_id": gas_source_id,
        "fuel_type": "NATURAL_GAS",
        "emission_rate": 0.38,
        "capacity_kw": 5000.0,
    })
    assert non_ren.status_code == 201, non_ren.text
    assert non_ren.json()["fuel_type"] == "NATURAL_GAS"

    # 4. Creating subtype with invalid parent must fail
    invalid_ren = await client.post("/api/renewable-sources", json={
        "source_id": "000000000000000000000000",
        "renewable_type": "WIND",
    })
    assert invalid_ren.status_code == 400


# ---------------------------------------------------------------------------
# Test 5: Grids and Linked Sources
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_grid_management(client):
    admin_token = await create_admin_and_login(client, "admin_grid@example.com")

    # Create source
    src = await client.post("/api/sources", json={
        "name": "East Grid Feeder Source",
        "source_type": "RENEWABLE",
        "capacity_kw": 8000.0,
    })
    source_id = src.json()["id"]

    # Create Grid
    grid_res = await client.post("/api/grids", json={
        "name": "Eastern Metropolitan Grid",
        "voltage_level": "400kV",
        "capacity_kw": 8000.0,
        "current_load_kw": 3100.0,
        "location": "Eastern Zone",
        "status": "ACTIVE",
        "source_id": source_id,
    })
    assert grid_res.status_code == 201, grid_res.text
    assert grid_res.json()["name"] == "Eastern Metropolitan Grid"


# ---------------------------------------------------------------------------
# Test 6: Charging Stations, Ports, and AC / DC Subtypes
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ports_and_ac_dc_subtypes(client):
    admin_token = await create_admin_and_login(client, "admin_port_test@example.com")

    # Create station
    stn_res = await client.post("/api/stations", json={
        "name": "Airport SuperHub",
        "station_code": "STN-AIRP",
        "address": "Terminal 2 EV Area",
        "city": "Metroville",
        "latitude": 40.6413,
        "longitude": -73.7781,
        "operating_hours": "24/7",
        "status": "operational",
    })
    assert stn_res.status_code == 201, stn_res.text
    station_id = stn_res.json()["id"]

    # Create Tariff
    tf_res = await client.post("/api/tariffs", json={
        "name": "SuperHub Dynamic",
        "price_per_kwh": 14.5,
        "valid_from": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
    })
    tariff_id = tf_res.json()["id"]

    # 1. Create AC Port (port 1)
    p1_res = await client.post("/api/ports", json={
        "station_id": station_id,
        "port_number": 1,
        "charger_type": "AC",
        "connector_type": "Type 2",
        "rated_power_kw": 22.0,
        "status": "operational",
        "tariff_id": tariff_id,
    })
    assert p1_res.status_code == 201, p1_res.text
    port1_id = p1_res.json()["id"]

    # Create AC Port Subtype
    ac_sub = await client.post("/api/ac-ports", json={
        "station_id": station_id,
        "port_number": 1,
        "connector_standard": "TYPE_2",
        "ac_phase": "THREE",
        "ac_power_kw": 22.0,
        "voltage": 400.0,
        "current": 32.0,
    })
    assert ac_sub.status_code == 201, ac_sub.text
    assert ac_sub.json()["connector_standard"] == "TYPE_2"

    # 2. Create DC Fast Port (port 2)
    p2_res = await client.post("/api/ports", json={
        "station_id": station_id,
        "port_number": 2,
        "charger_type": "DC_FAST",
        "connector_type": "CCS",
        "rated_power_kw": 150.0,
        "status": "operational",
        "tariff_id": tariff_id,
    })
    assert p2_res.status_code == 201, p2_res.text
    port2_id = p2_res.json()["id"]

    # Create DC Fast Port Subtype
    dc_sub = await client.post("/api/dc-fast-ports", json={
        "station_id": station_id,
        "port_number": 2,
        "dc_voltage": 800.0,
        "maximum_current": 200.0,
        "dc_power_kw": 150.0,
        "supported_standard": "CCS2",
    })
    assert dc_sub.status_code == 201, dc_sub.text
    assert dc_sub.json()["dc_voltage"] == 800.0

    # 3. Composite unique constraint check: duplicate port_number on same station must fail
    dup_port = await client.post("/api/ports", json={
        "station_id": station_id,
        "port_number": 1,
        "connector_type": "Type 2",
        "rated_power_kw": 22.0,
    })
    assert dup_port.status_code == 400

    # 4. AC/DC subtype on non-existent port must fail
    non_exist_ac = await client.post("/api/ac-ports", json={
        "station_id": station_id,
        "port_number": 99,
        "connector_standard": "TYPE_2",
        "ac_phase": "SINGLE",
    })
    assert non_exist_ac.status_code == 400


# ---------------------------------------------------------------------------
# Test 7: EV & Battery Status 1-to-1 Relationship
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ev_battery_status_relationship(client):
    cust_token = await create_customer_and_login(client, "cust_battery@example.com")

    # Register EV
    ev_res = await client.post("/api/evs", json={
        "model": "Kona Electric",
        "brand": "Hyundai",
        "registration_number": "BAT-777",
        "battery_capacity_kwh": 64.0,
        "connector_type": "CCS",
        "manufacturing_year": 2023,
    })
    assert ev_res.status_code == 201, ev_res.text
    ev_id = ev_res.json()["id"]

    # Register Battery Status
    b_res = await client.post("/api/battery-status", json={
        "ev_id": ev_id,
        "current_level": 78,
        "charging_level": 80,
        "health_status": "EXCELLENT",
        "temperature_c": 26.5,
    })
    assert b_res.status_code == 201, b_res.text
    assert b_res.json()["current_level"] == 78

    # Attempt duplicate battery status for same EV (must fail due to 1-to-1 unique)
    dup_b = await client.post("/api/battery-status", json={
        "ev_id": ev_id,
        "current_level": 79,
    })
    assert dup_b.status_code == 400


# ---------------------------------------------------------------------------
# Test 8: Maintenance & Subtypes (Preventive / Corrective)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_maintenance_subtypes(client):
    admin_token = await create_admin_and_login(client, "admin_maint_sub@example.com")

    stn = await client.post("/api/stations", json={
        "name": "West Plaza Station",
        "station_code": "STN-WEST",
        "address": "404 West Road",
        "city": "Metroville",
        "latitude": 40.7,
        "longitude": -74.1,
    })
    station_id = stn.json()["id"]

    # 1. Preventive Maintenance Parent & Subtype
    pm_parent = await client.post("/api/maintenance", json={
        "station_id": station_id,
        "maintenance_type": "PREVENTIVE",
        "title": "Quarterly Inverter Overhaul",
        "cost": 250.0,
        "status": "planned",
    })
    assert pm_parent.status_code == 201, pm_parent.text
    pm_id = pm_parent.json()["id"]

    prev_sub = await client.post("/api/preventive-maintenance", json={
        "maintenance_id": pm_id,
        "station_id": station_id,
        "maintenance_interval": 90,
        "next_due_date": "2026-12-01",
        "checklist": "Filter replacement; Fan lubricate; Thermal check",
        "inspection_result": "PASSED",
    })
    assert prev_sub.status_code == 201, prev_sub.text
    assert prev_sub.json()["maintenance_interval"] == 90

    # 2. Corrective Maintenance Parent & Subtype
    cm_parent = await client.post("/api/maintenance", json={
        "station_id": station_id,
        "maintenance_type": "CORRECTIVE",
        "title": "Ground Fault Emergency Repair",
        "cost": 500.0,
        "status": "in_progress",
    })
    assert cm_parent.status_code == 201, cm_parent.text
    cm_id = cm_parent.json()["id"]

    corr_sub = await client.post("/api/corrective-maintenance", json={
        "maintenance_id": cm_id,
        "station_id": station_id,
        "fault_description": "RCD tripping intermittently under 100A load",
        "repair_action": "Replaced ground isolator transformer module",
        "severity": "CRITICAL",
        "downtime": 6.5,
        "resolution_status": "IN_PROGRESS",
    })
    assert corr_sub.status_code == 201, corr_sub.text
    assert corr_sub.json()["severity"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Test 9: Schedules CRUD
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_schedules_crud(client):
    admin_token = await create_admin_and_login(client, "admin_sched@example.com")

    stn = await client.post("/api/stations", json={
        "name": "East Highway Hub",
        "station_code": "STN-EHW",
        "address": "Route 9 East",
        "city": "Springfield",
        "latitude": 42.1,
        "longitude": -72.5,
    })
    station_id = stn.json()["id"]

    now = datetime.now(timezone.utc)
    st = now + timedelta(days=2)
    et = st + timedelta(hours=10)

    sch = await client.post("/api/schedules", json={
        "station_id": station_id,
        "schedule_date": st.strftime("%Y-%m-%d"),
        "start_time": st.isoformat(),
        "end_time": et.isoformat(),
        "available_slots": 20,
        "schedule_type": "REGULAR",
        "is_available": True,
        "note": "Standard daylight hours",
    })
    assert sch.status_code == 201, sch.text
    assert sch.json()["available_slots"] == 20

    # Invalid time interval (end <= start) must fail
    inv_sch = await client.post("/api/schedules", json={
        "station_id": station_id,
        "start_time": et.isoformat(),
        "end_time": st.isoformat(),
    })
    assert inv_sch.status_code == 400


# ---------------------------------------------------------------------------
# Test 10: Notifications CRUD
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_notifications_crud(client):
    admin_token = await create_admin_and_login(client, "admin_notif@example.com")
    me = await client.get("/api/auth/me")
    uid = me.json()["id"]

    notif = await client.post("/api/notifications", json={
        "user_id": uid,
        "message": "Peak tariff in effect starting 5 PM",
        "notification_type": "ALERT",
    })
    assert notif.status_code == 201, notif.text
    nid = notif.json()["id"]
    assert notif.json()["is_read"] is False

    # Mark as read
    read_res = await client.post(f"/api/notifications/{nid}/read")
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True


# ---------------------------------------------------------------------------
# Test 11: Business Logic A: Booking Overlap & Concurrency Validation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_booking_availability_and_overlap(client):
    cust_token = await create_customer_and_login(client, "cust_book_test@example.com")
    me = await client.get("/api/auth/me")
    uid = me.json()["id"]

    # Register EV
    ev = await client.post("/api/evs", json={
        "model": "EV6",
        "brand": "Kia",
        "registration_number": "KIA-888",
        "battery_capacity_kwh": 77.4,
        "connector_type": "CCS",
    })
    ev_id = ev.json()["id"]

    # We need an admin to create station and port
    admin_token = await create_admin_and_login(client, "admin_book_setup@example.com")
    stn = await client.post("/api/stations", json={
        "name": "Central Plaza Chargers",
        "station_code": "STN-CENT",
        "address": "1 Central Blvd",
        "city": "Metroville",
        "latitude": 40.71,
        "longitude": -74.01,
    })
    station_id = stn.json()["id"]

    port = await client.post("/api/ports", json={
        "station_id": station_id,
        "port_number": 1,
        "connector_type": "CCS",
        "rated_power_kw": 50.0,
        "status": "operational",
    })
    port_id = port.json()["id"]

    # Re-login as customer
    await client.post("/api/auth/login", json={"email": "cust_book_test@example.com", "password": "CustPass123!"})

    future_start = (datetime.now(timezone.utc) + timedelta(days=5)).replace(minute=0, second=0, microsecond=0)
    future_end = future_start + timedelta(hours=2)

    # 1. Successful booking
    b1 = await client.post("/api/bookings", json={
        "ev_id": ev_id,
        "station_id": station_id,
        "port_id": port_id,
        "start_time": future_start.isoformat(),
        "end_time": future_end.isoformat(),
    })
    assert b1.status_code == 201, b1.text
    booking_id = b1.json()["id"]

    # 2. Overlapping booking on same port must fail
    overlap_b = await client.post("/api/bookings", json={
        "ev_id": ev_id,
        "station_id": station_id,
        "port_id": port_id,
        "start_time": (future_start + timedelta(minutes=30)).isoformat(),
        "end_time": (future_end + timedelta(minutes=30)).isoformat(),
    })
    assert overlap_b.status_code == 400

    # 3. Cancel booking releases availability
    cancel_res = await client.post(f"/api/bookings/{booking_id}/cancel")
    assert cancel_res.status_code == 200

    # 4. Now booking the same slot succeeds
    b2 = await client.post("/api/bookings", json={
        "ev_id": ev_id,
        "station_id": station_id,
        "port_id": port_id,
        "start_time": future_start.isoformat(),
        "end_time": future_end.isoformat(),
    })
    assert b2.status_code == 201, b2.text


# ---------------------------------------------------------------------------
# Test 12: Business Logic B: Charging Session & Automatic Bill Calculation
# Acceptance criterion: 20 kWh at ₹12/kWh must equal ₹240
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_session_billing_and_payment(client):
    admin_token = await create_admin_and_login(client, "admin_bill_test@example.com")

    # Create station and port
    stn = await client.post("/api/stations", json={
        "name": "Express SuperCharger",
        "station_code": "STN-EXP",
        "address": "Express Way Mile 12",
        "city": "Metroville",
        "latitude": 40.75,
        "longitude": -73.98,
    })
    station_id = stn.json()["id"]

    # Create tariff with price_per_kwh = 12.0
    tf = await client.post("/api/tariffs", json={
        "name": "Acceptance Tariff 12",
        "price_per_kwh": 12.0,
        "valid_from": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "is_active": True,
    })
    tariff_id = tf.json()["id"]

    port = await client.post("/api/ports", json={
        "station_id": station_id,
        "port_number": 1,
        "connector_type": "CCS",
        "rated_power_kw": 50.0,
        "status": "operational",
        "tariff_id": tariff_id,
    })
    port_id = port.json()["id"]

    # Customer logs in
    cust_token = await create_customer_and_login(client, "cust_session_bill@example.com")

    # Start session on available port
    sess_start = await client.post("/api/sessions/start", json={
        "port_id": port_id,
    })
    assert sess_start.status_code == 201, sess_start.text
    session_id = sess_start.json()["id"]
    assert sess_start.json()["status"] == "active"

    # End session with simulated 20 kWh consumption
    sess_end = await client.post(f"/api/sessions/{session_id}/end", json={
        "energy_delivered_kwh": 20.0,
    })
    assert sess_end.status_code == 200, sess_end.text
    session_data = sess_end.json()

    # Exact billing validation
    assert session_data["energy_delivered_kwh"] == 20.0
    assert session_data["tariff_price_per_kwh"] == 12.0
    assert session_data["total_amount"] == 240.0
    assert session_data["status"] == "completed"

    # Verify payment record was automatically created with amount 240.0
    pay_res = await client.get("/api/payments")
    assert pay_res.status_code == 200
    user_payments = pay_res.json()["items"]
    assert any(p["session_id"] == session_id and p["amount"] == 240.0 for p in user_payments)
