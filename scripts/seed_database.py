#!/usr/bin/env python3
"""Idempotent seed script for all 22 Smart EV entities in MongoDB.

Reads configuration from backend/.env (MONGODB_URI, MONGODB_DB, SEED_*).
Safe to run multiple times: existing records are never duplicated.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import ASCENDING, DESCENDING
from pymongo.mongo_client import MongoClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
load_dotenv(os.path.join(ROOT, "backend", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:changeme@localhost:27017/smart_ev_charging?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "smart_ev_charging")

SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@evcharging.local")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "AdminPass123!")
SEED_ADMIN_FULL_NAME = os.getenv("SEED_ADMIN_FULL_NAME", "System Administrator")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def now():
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def upsert(db, collection, filter_doc, doc):
    existing = db[collection].find_one(filter_doc)
    if existing:
        return str(existing["_id"])
    res = db[collection].insert_one(doc)
    return str(res.inserted_id)


def main():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]

    # Initialize collections and indexes via backend helper logic
    from app.database import ALL_COLLECTIONS, BOOKING_SLOT_LOCKS, init_indexes
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient

    async def _async_init():
        motor_client = AsyncIOMotorClient(MONGODB_URI)
        motor_db = motor_client[MONGODB_DB]
        await init_indexes(motor_db)
        motor_client.close()

    try:
        asyncio.run(_async_init())
    except Exception as e:
        print(f"Index initialization warning: {e}")

    tz = timezone.utc
    now_dt = now()

    SAMPLE_BOOKING_START = datetime(2026, 11, 1, 10, 0, 0, tzinfo=tz)
    SAMPLE_BOOKING_END = SAMPLE_BOOKING_START + timedelta(hours=2)
    SAMPLE_SESSION_START = datetime(2026, 10, 1, 10, 0, 0, tzinfo=tz)
    SAMPLE_SESSION_END = SAMPLE_SESSION_START + timedelta(hours=1)

    print("Seeding all 22 Smart EV entities...")

    # -------------------------------------------------------------------------
    # 1. EV_USER (users)
    # -------------------------------------------------------------------------
    customer_defs = [
        ("alice@example.com", "Alice", "Customer", "+1-555-0001", "101 Elm St, Springfield", "1992-04-12", 1),
        ("bob@example.com", "Bob", "Smith", "+1-555-0002", "202 Maple Ave, Springfield", "1988-08-25", 2),
        ("carol@example.com", "Carol", "Danvers", "+1-555-0003", "303 Oak Lane, Metroville", "1995-01-30", 3),
        ("dave@example.com", "Dave", "Miller", "+1-555-0004", "404 Pine Rd, Greenfield", "1984-11-15", 4),
        ("eve@example.com", "Eve", "Wilson", "+1-555-0005", "505 Cedar Blvd, Greenfield", "1991-07-22", 5),
    ]
    customer_ids = {}
    for email, fn, ln, phone, addr, dob, uid in customer_defs:
        doc = {
            "user_id": uid,
            "email": email,
            "password_hash": hash_password("CustomerPass123!"),
            "full_name": f"{fn} {ln}",
            "first_name": fn,
            "last_name": ln,
            "phone": phone,
            "address": addr,
            "date_of_birth": dob,
            "role": "customer",
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        }
        customer_ids[email] = upsert(db, "users", {"email": email}, doc)

    # -------------------------------------------------------------------------
    # 2. ADMIN (admins)
    # -------------------------------------------------------------------------
    admin_user_id = upsert(
        db,
        "users",
        {"email": SEED_ADMIN_EMAIL},
        {
            "user_id": 999,
            "email": SEED_ADMIN_EMAIL,
            "password_hash": hash_password(SEED_ADMIN_PASSWORD),
            "full_name": SEED_ADMIN_FULL_NAME,
            "first_name": "System",
            "last_name": "Administrator",
            "phone": "+1-555-0000",
            "address": "Headquarters, Central Station",
            "date_of_birth": "1980-01-01",
            "role": "admin",
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )
    admin_id = upsert(
        db,
        "admins",
        {"email": SEED_ADMIN_EMAIL},
        {
            "admin_id": 1,
            "user_id": admin_user_id,
            "email": SEED_ADMIN_EMAIL,
            "admin_name": SEED_ADMIN_FULL_NAME,
            "full_name": SEED_ADMIN_FULL_NAME,
            "phone_no": "+1-555-0000",
            "phone": "+1-555-0000",
            "role": "SUPER_ADMIN",
            "experience": 8,
            "privileges": ["manage_users", "manage_stations", "manage_tariffs", "manage_payments", "manage_maintenance"],
            "status": "active",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    alice_id = customer_ids["alice@example.com"]
    bob_id = customer_ids["bob@example.com"]

    # -------------------------------------------------------------------------
    # 7. USER_PHONE (user_phones)
    # -------------------------------------------------------------------------
    phone_defs = [
        (alice_id, "+1-555-0001", "Mobile", True),
        (alice_id, "+1-555-1001", "Work", False),
        (bob_id, "+1-555-0002", "Mobile", True),
        (customer_ids["carol@example.com"], "+1-555-0003", "Mobile", True),
        (customer_ids["dave@example.com"], "+1-555-0004", "Mobile", True),
    ]
    for uid, num, label, is_prim in phone_defs:
        upsert(
            db,
            "user_phones",
            {"user_id": uid, "number": num},
            {
                "user_id": uid,
                "number": num,
                "phone_no": num,
                "label": label,
                "phone_type": label,
                "is_primary": is_prim,
                "created_at": now_dt,
                "updated_at": now_dt,
            },
        )

    # -------------------------------------------------------------------------
    # 3. TARIFF (tariffs)
    # -------------------------------------------------------------------------
    tariff_defs = [
        ("Standard", 12.0, 15.0, 8.0, now_dt, now_dt + timedelta(days=365), True, 1),
        ("Off-Peak", 8.0, 12.0, 6.0, now_dt, now_dt + timedelta(days=365), True, 2),
        ("Premium Fast", 18.0, 22.0, 14.0, now_dt, now_dt + timedelta(days=365), True, 3),
    ]
    tariff_ids = {}
    for name, price, peak, off_peak, vf, vt, active, tid in tariff_defs:
        doc = {
            "tariff_id": tid,
            "name": name,
            "tariff_name": name,
            "price_per_kwh": price,
            "rate_per_kwh": price,
            "peak_hour_rate": peak,
            "off_peak_rate": off_peak,
            "valid_from": vf,
            "start_date": vf,
            "valid_to": vt,
            "end_date": vt,
            "is_active": active,
            "status": "ACTIVE",
            "description": f"{name} tariff plan",
            "created_at": now_dt,
            "updated_at": now_dt,
        }
        tariff_ids[name] = upsert(db, "tariffs", {"name": name}, doc)

    # -------------------------------------------------------------------------
    # 4. SOURCE (sources)
    # -------------------------------------------------------------------------
    source_defs = [
        ("Solar Farm Alpha", "RENEWABLE", 1500.0, "kW", "ACTIVE", 3500.0, "Utility-scale solar array", 1),
        ("Wind Station Beta", "RENEWABLE", 2500.0, "kW", "ACTIVE", 6200.0, "Coastal wind turbine farm", 2),
        ("Gas Peaker Plant Gamma", "NON_RENEWABLE", 3000.0, "kW", "ACTIVE", 8900.0, "Natural gas backup generation", 3),
    ]
    source_ids = {}
    for sname, stype, cap, unit, st, gen, desc, sid in source_defs:
        doc = {
            "source_id": sid,
            "name": sname,
            "source_name": sname,
            "source_type": stype,
            "capacity": cap,
            "capacity_kw": cap,
            "unit": unit,
            "status": st,
            "energy_generated_kwh": gen,
            "description": desc,
            "created_at": now_dt,
            "updated_at": now_dt,
        }
        source_ids[sname] = upsert(db, "sources", {"name": sname}, doc)

    # -------------------------------------------------------------------------
    # 19. RENEWABLE_SOURCE (renewable_sources)
    # -------------------------------------------------------------------------
    upsert(
        db,
        "renewable_sources",
        {"source_id": source_ids["Solar Farm Alpha"]},
        {
            "source_id": source_ids["Solar Farm Alpha"],
            "name": "Solar Farm Alpha",
            "source_type": "RENEWABLE",
            "renewable_type": "SOLAR",
            "generation_efficiency": 22.5,
            "capacity_kw": 1500.0,
            "energy_generated_kwh": 3500.0,
            "status": "ACTIVE",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )
    upsert(
        db,
        "renewable_sources",
        {"source_id": source_ids["Wind Station Beta"]},
        {
            "source_id": source_ids["Wind Station Beta"],
            "name": "Wind Station Beta",
            "source_type": "RENEWABLE",
            "renewable_type": "WIND",
            "generation_efficiency": 45.0,
            "capacity_kw": 2500.0,
            "energy_generated_kwh": 6200.0,
            "status": "ACTIVE",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 20. NON_RENEWABLE_SOURCE (non_renewable_sources)
    # -------------------------------------------------------------------------
    upsert(
        db,
        "non_renewable_sources",
        {"source_id": source_ids["Gas Peaker Plant Gamma"]},
        {
            "source_id": source_ids["Gas Peaker Plant Gamma"],
            "name": "Gas Peaker Plant Gamma",
            "source_type": "NON_RENEWABLE",
            "fuel_type": "NATURAL_GAS",
            "emission_rate": 0.42,
            "capacity_kw": 3000.0,
            "energy_generated_kwh": 8900.0,
            "status": "ACTIVE",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 8. GRID (grids)
    # -------------------------------------------------------------------------
    grid_id = upsert(
        db,
        "grids",
        {"name": "Main Metro Grid"},
        {
            "grid_id": 1,
            "name": "Main Metro Grid",
            "grid_name": "Main Metro Grid",
            "voltage_level": "400kV",
            "capacity": 10000.0,
            "capacity_kw": 10000.0,
            "current_load": 4200.0,
            "current_load_kw": 4200.0,
            "location": "Metroville Sector 4",
            "status": "ACTIVE",
            "source_id": source_ids["Solar Farm Alpha"],
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 5. CHARGING_STATION (charging_stations)
    # -------------------------------------------------------------------------
    station_defs = [
        ("Downtown EV Hub", "STN-001", "123 Main Street", "Metroville", 40.7128, -74.006, "06:00 - 23:00", 1),
        ("Greenfield Plaza Chargers", "STN-002", "456 Park Avenue", "Greenfield", 34.0522, -118.2437, "24/7", 2),
        ("Highway Rest Stop North", "STN-003", "789 Interstate 95", "Springfield", 51.5074, -0.1278, "24/7", 3),
    ]
    station_ids = {}
    for sname, scode, addr, city, lat, lon, ophours, sid in station_defs:
        doc = {
            "station_id": sid,
            "name": sname,
            "station_name": sname,
            "station_code": scode,
            "address": addr,
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "operating_hours": ophours,
            "grid_id": grid_id,
            "status": "operational",
            "total_ports": 0,
            "created_at": now_dt,
            "updated_at": now_dt,
        }
        station_ids[scode] = upsert(db, "charging_stations", {"station_code": scode}, doc)

    # -------------------------------------------------------------------------
    # 9. CHARGING_PORT (charging_ports)
    # -------------------------------------------------------------------------
    port_defs = [
        ("STN-001", 1, "CCS", "DC_FAST", 50.0, "operational", tariff_ids["Standard"], 1),
        ("STN-001", 2, "Type 2", "AC", 22.0, "operational", tariff_ids["Off-Peak"], 2),
        ("STN-001", 3, "CCS", "DC_FAST", 150.0, "operational", tariff_ids["Premium Fast"], 3),
        ("STN-002", 1, "CCS", "DC_FAST", 150.0, "operational", tariff_ids["Premium Fast"], 4),
        ("STN-002", 2, "Type 2", "AC", 22.0, "operational", tariff_ids["Off-Peak"], 5),
        ("STN-003", 1, "CCS", "DC_FAST", 50.0, "operational", tariff_ids["Standard"], 6),
        ("STN-003", 2, "Type 2", "AC", 22.0, "operational", tariff_ids["Standard"], 7),
    ]
    port_ids = {}
    for code, num, conn, ctype, kw, st, tid, pid_int in port_defs:
        doc = {
            "port_id": pid_int,
            "station_id": station_ids[code],
            "station_code": code,
            "port_number": num,
            "connector_type": conn,
            "charger_type": ctype,
            "power_output": kw,
            "rated_power_kw": kw,
            "status": st,
            "availability_status": "AVAILABLE",
            "tariff_id": tid,
            "created_at": now_dt,
            "updated_at": now_dt,
        }
        pid = upsert(db, "charging_ports", {"station_id": station_ids[code], "port_number": num}, doc)
        port_ids[f"{code}-{num}"] = pid

    # Update total_ports count on stations
    for code, sid in station_ids.items():
        cnt = db["charging_ports"].count_documents({"station_id": sid})
        db["charging_stations"].update_one({"_id": db["charging_stations"].find_one({"station_code": code})["_id"]}, {"$set": {"total_ports": cnt}})

    # -------------------------------------------------------------------------
    # 10. AC_PORT (ac_ports)
    # -------------------------------------------------------------------------
    ac_port_defs = [
        ("STN-001", 2, "TYPE_2", "THREE", 22.0, 400.0, 32.0),
        ("STN-002", 2, "TYPE_2", "THREE", 22.0, 400.0, 32.0),
        ("STN-003", 2, "TYPE_2", "SINGLE", 7.4, 230.0, 32.0),
    ]
    for code, num, std, phase, kw, volt, amp in ac_port_defs:
        upsert(
            db,
            "ac_ports",
            {"station_id": station_ids[code], "port_number": num},
            {
                "station_id": station_ids[code],
                "port_number": num,
                "port_id": port_ids[f"{code}-{num}"],
                "connector_standard": std,
                "ac_phase": phase,
                "ac_power_kw": kw,
                "voltage": volt,
                "current": amp,
                "created_at": now_dt,
                "updated_at": now_dt,
            },
        )

    # -------------------------------------------------------------------------
    # 11. DC_FAST_PORT (dc_fast_ports)
    # -------------------------------------------------------------------------
    dc_port_defs = [
        ("STN-001", 1, 400.0, 125.0, 50.0, "CCS1"),
        ("STN-001", 3, 800.0, 200.0, 150.0, "CCS2"),
        ("STN-002", 1, 800.0, 200.0, 150.0, "CCS2"),
        ("STN-003", 1, 400.0, 125.0, 50.0, "CCS2"),
    ]
    for code, num, volt, amp, kw, std in dc_port_defs:
        upsert(
            db,
            "dc_fast_ports",
            {"station_id": station_ids[code], "port_number": num},
            {
                "station_id": station_ids[code],
                "port_number": num,
                "port_id": port_ids[f"{code}-{num}"],
                "dc_voltage": volt,
                "maximum_current": amp,
                "dc_power_kw": kw,
                "supported_standard": std,
                "created_at": now_dt,
                "updated_at": now_dt,
            },
        )

    # -------------------------------------------------------------------------
    # 6. EV (evs)
    # -------------------------------------------------------------------------
    ev_defs = [
        (alice_id, "Tesla", "Model 3", "ABC-1234", 75.0, "CCS", 2022, 1),
        (alice_id, "Nissan", "Leaf", "XYZ-5678", 40.0, "CHAdeMO", 2021, 2),
        (bob_id, "Hyundai", "Ioniq 5", "ION-9012", 77.4, "CCS", 2023, 3),
        (customer_ids["carol@example.com"], "MG", "ZS EV", "MG-3456", 51.1, "Type 2", 2022, 4),
        (customer_ids["dave@example.com"], "Tesla", "Model Y", "TY-7890", 82.0, "CCS", 2024, 5),
    ]
    ev_ids = {}
    for owner, brand, model, reg, cap, conn, yr, evid in ev_defs:
        doc = {
            "ev_id": evid,
            "owner_id": owner,
            "user_id": owner,
            "brand": brand,
            "manufacturer": brand,
            "model": model,
            "registration_number": reg,
            "vehicle_number": reg,
            "battery_capacity": cap,
            "battery_capacity_kwh": cap,
            "connector_type": conn,
            "manufacturing_year": yr,
            "manufacture_year": yr,
            "is_active": True,
            "status": "ACTIVE",
            "created_at": now_dt,
            "updated_at": now_dt,
        }
        ev_ids[reg] = upsert(db, "evs", {"registration_number": reg}, doc)

    # -------------------------------------------------------------------------
    # 18. BATTERY_STATUS (battery_status)
    # -------------------------------------------------------------------------
    battery_defs = [
        ("ABC-1234", 82, 85, "GOOD", 31.0, 1),
        ("XYZ-5678", 55, 60, "FAIR", 29.5, 2),
        ("ION-9012", 90, 92, "EXCELLENT", 28.0, 3),
        ("MG-3456", 67, 70, "GOOD", 30.5, 4),
        ("TY-7890", 94, 95, "EXCELLENT", 27.5, 5),
    ]
    for reg, cur, chg, hlth, temp, bsid in battery_defs:
        upsert(
            db,
            "battery_status",
            {"ev_id": ev_ids[reg]},
            {
                "battery_status_id": bsid,
                "ev_id": ev_ids[reg],
                "current_level": cur,
                "battery_percentage": float(cur),
                "charging_level": chg,
                "health_status": hlth,
                "temperature_c": temp,
                "last_updated": now_dt,
                "recorded_at": now_dt,
                "created_at": now_dt,
                "updated_at": now_dt,
            },
        )

    # -------------------------------------------------------------------------
    # 12. BOOKING (bookings)
    # -------------------------------------------------------------------------
    booking_id = upsert(
        db,
        "bookings",
        {"user_id": alice_id, "port_id": port_ids["STN-001-1"], "start_time": SAMPLE_BOOKING_START},
        {
            "booking_id": 1,
            "user_id": alice_id,
            "ev_id": ev_ids["ABC-1234"],
            "station_id": station_ids["STN-001"],
            "port_id": port_ids["STN-001-1"],
            "port_number": 1,
            "booking_date": SAMPLE_BOOKING_START.strftime("%Y-%m-%d"),
            "booking_time": SAMPLE_BOOKING_START,
            "start_time": SAMPLE_BOOKING_START,
            "end_time": SAMPLE_BOOKING_END,
            "status": "confirmed",
            "booking_status": "CONFIRMED",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 13. CHARGING_SESSION (charging_sessions)
    # -------------------------------------------------------------------------
    session_id = upsert(
        db,
        "charging_sessions",
        {"port_id": port_ids["STN-001-1"], "started_at": SAMPLE_SESSION_START},
        {
            "session_id": 1,
            "booking_id": booking_id,
            "user_id": alice_id,
            "ev_id": ev_ids["ABC-1234"],
            "port_id": port_ids["STN-001-1"],
            "started_at": SAMPLE_SESSION_START,
            "start_time": SAMPLE_SESSION_START,
            "ended_at": SAMPLE_SESSION_END,
            "end_time": SAMPLE_SESSION_END,
            "energy_delivered_kwh": 20.0,
            "energy_consumed_kwh": 20.0,
            "energy_consumed": 20.0,
            "total_amount": 240.0,
            "tariff_price_per_kwh": 12.0,
            "status": "completed",
            "session_status": "COMPLETED",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 14. PAYMENT (payments)
    # -------------------------------------------------------------------------
    upsert(
        db,
        "payments",
        {"session_id": session_id},
        {
            "payment_id": 1,
            "session_id": session_id,
            "user_id": alice_id,
            "amount": 240.0,
            "payment_method": "simulated",
            "payment_mode": "UPI",
            "payment_date": SAMPLE_SESSION_END.strftime("%Y-%m-%d"),
            "transaction_reference": f"EV-{session_id[-8:]}-SEED",
            "status": "completed",
            "payment_status": "COMPLETED",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 15. SCHEDULE (schedules)
    # -------------------------------------------------------------------------
    schedule_defs = [
        ("STN-001", "STN-001-1", now_dt + timedelta(days=1), now_dt + timedelta(days=1, hours=8), 12, 1),
        ("STN-002", "STN-002-1", now_dt + timedelta(days=2), now_dt + timedelta(days=2, hours=8), 16, 2),
        ("STN-003", "STN-003-1", now_dt + timedelta(days=3), now_dt + timedelta(days=3, hours=8), 10, 3),
    ]
    for scode, pcode, st_t, end_t, slots, sch_id in schedule_defs:
        upsert(
            db,
            "schedules",
            {"station_id": station_ids[scode], "schedule_id": sch_id},
            {
                "schedule_id": sch_id,
                "station_id": station_ids[scode],
                "port_id": port_ids[pcode],
                "schedule_date": st_t.strftime("%Y-%m-%d"),
                "start_time": st_t,
                "end_time": end_t,
                "available_slots": slots,
                "schedule_type": "REGULAR",
                "is_available": True,
                "status": "ACTIVE",
                "note": f"Operating window for {scode}",
                "description": f"Operating window for {scode}",
                "created_at": now_dt,
                "updated_at": now_dt,
            },
        )

    # -------------------------------------------------------------------------
    # 16. MAINTENANCE (maintenance)
    # -------------------------------------------------------------------------
    maint_id = upsert(
        db,
        "maintenance",
        {"station_id": station_ids["STN-002"], "title": "Port 2 cable inspection"},
        {
            "maintenance_id": 1,
            "station_id": station_ids["STN-002"],
            "port_id": port_ids["STN-002-2"],
            "admin_id": admin_id,
            "maintenance_type": "PREVENTIVE",
            "title": "Port 2 cable inspection",
            "description": "Inspect CCS cable for wear and electrical insulation",
            "scheduled_date": now_dt + timedelta(days=2),
            "maintenance_date": (now_dt + timedelta(days=2)).strftime("%Y-%m-%d"),
            "cost": 150.0,
            "status": "planned",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    maint_corr_id = upsert(
        db,
        "maintenance",
        {"station_id": station_ids["STN-001"], "title": "Connector Lock Repair"},
        {
            "maintenance_id": 2,
            "station_id": station_ids["STN-001"],
            "port_id": port_ids["STN-001-1"],
            "admin_id": admin_id,
            "maintenance_type": "CORRECTIVE",
            "title": "Connector Lock Repair",
            "description": "Port 1 mechanical latch sensor malfunction",
            "scheduled_date": now_dt + timedelta(days=1),
            "maintenance_date": (now_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            "cost": 320.0,
            "status": "in_progress",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 21. PREVENTIVE_MAINTENANCE (preventive_maintenance)
    # -------------------------------------------------------------------------
    upsert(
        db,
        "preventive_maintenance",
        {"maintenance_id": maint_id},
        {
            "maintenance_id": maint_id,
            "station_id": station_ids["STN-002"],
            "maintenance_interval": 30,
            "next_due_date": (now_dt + timedelta(days=32)).strftime("%Y-%m-%d"),
            "checklist": "Visual cable check; Ground continuity; RCD trip test; Connector clean",
            "inspection_result": "PASSED",
            "title": "Port 2 cable inspection",
            "description": "Routine 30-day preventive inspection",
            "status": "scheduled",
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 22. CORRECTIVE_MAINTENANCE (corrective_maintenance)
    # -------------------------------------------------------------------------
    upsert(
        db,
        "corrective_maintenance",
        {"maintenance_id": maint_corr_id},
        {
            "maintenance_id": maint_corr_id,
            "station_id": station_ids["STN-001"],
            "port_id": port_ids["STN-001-1"],
            "fault_title": "Connector Lock Repair",
            "fault_description": "Mechanical latch failing to engage EV socket cleanly",
            "repair_action": "Replaced solenoid actuator and recalibrated latch position",
            "severity": "HIGH",
            "repair_date": (now_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
            "downtime": 4.5,
            "resolution_status": "IN_PROGRESS",
            "status": "open",
            "reported_date": now_dt,
            "created_at": now_dt,
            "updated_at": now_dt,
        },
    )

    # -------------------------------------------------------------------------
    # 17. NOTIFICATION (notifications)
    # -------------------------------------------------------------------------
    notif_defs = [
        (alice_id, "Welcome to Smart EV Charging!", "WELCOME", True, 1),
        (alice_id, "Your charging reservation for Downtown EV Hub is confirmed.", "BOOKING_CONFIRMED", False, 2),
        (bob_id, "Your charging session has completed successfully.", "SESSION_COMPLETE", False, 3),
        (customer_ids["carol@example.com"], "System maintenance scheduled for Station STN-002.", "ALERT", False, 4),
        (customer_ids["dave@example.com"], "Low battery notification: your EV is below 20%.", "BATTERY_WARNING", False, 5),
    ]
    for uid, msg, ntype, read_st, nid in notif_defs:
        upsert(
            db,
            "notifications",
            {"user_id": uid, "message": msg},
            {
                "notification_id": nid,
                "user_id": uid,
                "message": msg,
                "notification_type": ntype,
                "is_read": read_st,
                "read_status": "READ" if read_st else "UNREAD",
                "sent_date": now_dt,
                "created_at": now_dt,
                "updated_at": now_dt,
            },
        )

    print("\n--- Seeding Summary Across All 22 Entities ---")
    for c in sorted(ALL_COLLECTIONS):
        count = db[c].count_documents({})
        print(f"  ✓ {c.ljust(26)}: {count} document(s)")

    print("\nSeed successfully completed!")
    print(f"Admin login:    {SEED_ADMIN_EMAIL} / {SEED_ADMIN_PASSWORD}")
    print(f"Customer login: alice@example.com / CustomerPass123!")
    client.close()


if __name__ == "__main__":
    main()
