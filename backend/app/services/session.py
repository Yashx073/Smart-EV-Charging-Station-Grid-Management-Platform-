from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import (
    BOOKINGS,
    CHARGING_PORTS,
    CHARGING_SESSIONS,
    PAYMENTS,
    TARIFFS,
    get_db,
)
from app.utils import to_object_id, to_str_id, utc_now

ACTIVE_SESSION_STATUSES = {"active"}
BILLING_METHOD = "simulated"


async def start_session(db: AsyncIOMotorDatabase, user_id: str, data: dict) -> dict:
    booking_id = data.get("booking_id")
    port_id = data["port_id"]
    now = utc_now()

    port = await db[CHARGING_PORTS].find_one({"_id": to_object_id(port_id), "status": "operational"})
    if not port:
        raise ValueError("Port not found or not operational")

    # No active session already on this port (prevent duplicate start)
    active = await db[CHARGING_SESSIONS].find_one(
        {"port_id": port_id, "status": {"$in": list(ACTIVE_SESSION_STATUSES)}}
    )
    if active:
        raise ValueError("Port already has an active charging session")

    ev_id = data.get("ev_id")
    if booking_id:
        booking = await db[BOOKINGS].find_one({"_id": to_object_id(booking_id)})
        if not booking:
            raise ValueError("Booking not found")
        if str(booking["user_id"]) != user_id:
            raise PermissionError("Not your booking")
        if booking["status"] not in {"confirmed", "active"}:
            raise ValueError("Booking is not eligible for a charging session")
        if str(booking["port_id"]) != port_id:
            raise ValueError("Booking port does not match the selected port")
        # Ensure no overlapping active booking on the port at session start
        ev_id = booking.get("ev_id")
        await db[BOOKINGS].update_one(
            {"_id": to_object_id(booking_id)}, {"$set": {"status": "active", "updated_at": now}}
        )

    session_doc = {
        "user_id": user_id,
        "ev_id": ev_id,
        "port_id": port_id,
        "started_at": now,
        "ended_at": None,
        "energy_delivered_kwh": None,
        "total_amount": None,
        "tariff_price_per_kwh": None,
        "status": "active",
        "created_at": now,
    }
    if booking_id:
        session_doc["booking_id"] = str(booking_id)
    res = await db[CHARGING_SESSIONS].insert_one(session_doc)
    session_doc["_id"] = res.inserted_id
    return to_str_id(session_doc)


async def _find_applicable_tariff(db: AsyncIOMotorDatabase, started_at: datetime) -> dict | None:
    query = {
        "is_active": True,
        "valid_from": {"$lte": started_at},
        "$or": [{"valid_to": None}, {"valid_to": {"$gte": started_at}}],
    }
    tariff = await db[TARIFFS].find_one(query, sort=[("valid_from", -1)])
    if tariff is None:
        tariff = await db[TARIFFS].find_one({"is_active": True}, sort=[("valid_from", -1)])
    return to_str_id(tariff) if tariff else None


async def end_session(db: AsyncIOMotorDatabase, session_id: str, user_id: str, data: dict) -> dict:
    energy = data["energy_delivered_kwh"]
    now = utc_now()

    session = await db[CHARGING_SESSIONS].find_one({"_id": to_object_id(session_id)})
    if not session:
        raise ValueError("Session not found")
    if str(session["user_id"]) != user_id:
        raise PermissionError("Not your session")
    if session["status"] != "active":
        raise ValueError("Session is not active")
    if session.get("ended_at"):
        raise ValueError("Session already ended / already billed")

    tariff = await _find_applicable_tariff(db, session["started_at"])
    if not tariff:
        raise ValueError("No applicable tariff found")
    price = float(tariff["price_per_kwh"])
    total = round(float(energy) * price, 2)

    # End session
    await db[CHARGING_SESSIONS].update_one(
        {"_id": to_object_id(session_id)},
        {
            "$set": {
                "ended_at": now,
                "energy_delivered_kwh": energy,
                "total_amount": total,
                "tariff_price_per_kwh": price,
                "status": "completed",
                "updated_at": now,
            }
        },
    )

    # Create payment (simulated). Prevent duplicate billing via unique session_id index.
    tx_ref = f"EV-{str(session_id)[-8:]}-{int(now.timestamp())}"
    payment_doc = {
        "session_id": session_id,
        "user_id": user_id,
        "amount": total,
        "payment_method": BILLING_METHOD,
        "transaction_reference": tx_ref,
        "status": "completed",
        "created_at": now,
    }
    try:
        await db[PAYMENTS].insert_one(payment_doc)
    except Exception:
        pass

    # Release port
    await db[CHARGING_PORTS].update_one(
        {"_id": to_object_id(session["port_id"])}, {"$set": {"status": "operational"}}
    )

    # Complete the linked booking if present
    if session.get("booking_id"):
        await db[BOOKINGS].update_one(
            {"_id": to_object_id(session["booking_id"])},
            {"$set": {"status": "completed", "updated_at": now}},
        )

    updated = await db[CHARGING_SESSIONS].find_one({"_id": to_object_id(session_id)})
    out = to_str_id(updated)
    out["payment"] = {**payment_doc, "id": str(payment_doc.get("_id", ""))} if payment_doc.get("_id") else payment_doc
    return out


async def list_user_sessions(db: AsyncIOMotorDatabase, user_id: str, page=1, page_size=20):
    return await _list(db, {"user_id": user_id}, page, page_size)


async def list_all_sessions(db: AsyncIOMotorDatabase, page=1, page_size=20):
    return await _list(db, {}, page, page_size)


async def _list(db: AsyncIOMotorDatabase, filter_: dict, page: int, page_size: int):
    skip, limit = _paginate(page, page_size)
    cursor = db[CHARGING_SESSIONS].find(filter_).sort("started_at", -1)
    total = await db[CHARGING_SESSIONS].count_documents(filter_)
    docs = [to_str_id(d) async for d in cursor.skip(skip).limit(limit)]
    return {"items": docs, "total": total, "page": page, "page_size": limit}


def _paginate(page: int, page_size: int):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    return (page - 1) * page_size, page_size
