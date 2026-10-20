from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import (
    BOOKING_SLOT_LOCKS,
    BOOKINGS,
    CHARGING_PORTS,
    CHARGING_STATIONS,
    EVS,
    get_db,
)
from app.utils import to_object_id, to_str_id, utc_now

SLOT_MINUTES = 30
BLOCKING_STATUSES = {"pending", "confirmed", "active"}
CANCELLABLE_STATUSES = {"pending", "confirmed"}


def _slot_starts(start: datetime, end: datetime) -> list[datetime]:
    """Return 30-minute slot starts covering [start, end)."""
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    # floor start to slot boundary
    minute = start.minute - (start.minute % SLOT_MINUTES)
    slot = start.replace(minute=minute, second=0, microsecond=0)
    slots: list[datetime] = []
    while slot < end:
        slots.append(slot)
        slot += timedelta(minutes=SLOT_MINUTES)
    return slots


async def create_booking(db: AsyncIOMotorDatabase, user_id: str, data: dict) -> dict:
    oid_user = to_object_id(user_id)
    ev_id = data["ev_id"]
    station_id = data["station_id"]
    port_id = data["port_id"]
    start_time = data["start_time"]
    end_time = data["end_time"]

    start_time = start_time.astimezone(timezone.utc)
    end_time = end_time.astimezone(timezone.utc)
    now = utc_now()

    # 1. EV belongs to customer
    ev = await db[EVS].find_one({"_id": to_object_id(ev_id), "owner_id": user_id})
    if not ev:
        raise ValueError("EV not found or does not belong to you")

    # 2. Station and port exist and operational
    station = await db[CHARGING_STATIONS].find_one(
        {"_id": to_object_id(station_id), "status": "operational"}
    )
    if not station:
        raise ValueError("Charging station not found or not operational")
    port = await db[CHARGING_PORTS].find_one(
        {"_id": to_object_id(port_id), "station_id": station_id, "status": "operational"}
    )
    if not port:
        raise ValueError("Charging port not found or not operational")

    # 3. Valid future interval
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")
    if start_time <= now:
        raise ValueError("start_time must be in the future")

    # 4. Overlap check (blocking statuses)
    overlap = await db[BOOKINGS].find_one(
        {
            "port_id": port_id,
            "status": {"$in": list(BLOCKING_STATUSES)},
            "$and": [
                {"start_time": {"$lt": end_time}},
                {"end_time": {"$gt": start_time}},
            ],
        }
    )
    if overlap:
        raise ValueError("Port is already booked for the requested time slot")

    # 5. Concurrency control: reserve 30-minute slots via unique index.
    slots = _slot_starts(start_time, end_time)
    inserted: list[dict] = []
    try:
        for slot in slots:
            lock_doc = {
                "port_id": port_id,
                "slot_start": slot,
                "booking_id": None,  # filled after booking insert
                "created_at": now,
                "expires_at": end_time,
            }
            res = await db[BOOKING_SLOT_LOCKS].insert_one(lock_doc)
            lock_doc["_id"] = res.inserted_id
            inserted.append(lock_doc)
    except Exception:
        # Duplicate key = another request reserved a slot first. Roll back.
        for lock in inserted:
            await db[BOOKING_SLOT_LOCKS].delete_one({"_id": lock["_id"]})
        raise ValueError("Port is already booked for the requested time slot (concurrent booking)")

    # 6. Create booking
    booking_doc = {
        "user_id": user_id,
        "ev_id": ev_id,
        "station_id": station_id,
        "port_id": port_id,
        "start_time": start_time,
        "end_time": end_time,
        "status": "confirmed",
        "created_at": now,
    }
    res = await db[BOOKINGS].insert_one(booking_doc)
    booking_doc["_id"] = res.inserted_id

    # Link slot locks to booking
    for lock in inserted:
        await db[BOOKING_SLOT_LOCKS].update_one(
            {"_id": lock["_id"]}, {"$set": {"booking_id": str(res.inserted_id)}}
        )

    return to_str_id(booking_doc)


async def cancel_booking(db: AsyncIOMotorDatabase, booking_id: str, user_id: str) -> dict:
    oid = to_object_id(booking_id)
    booking = await db[BOOKINGS].find_one({"_id": oid})
    if not booking:
        raise ValueError("Booking not found")
    if str(booking["user_id"]) != user_id:
        raise PermissionError("Not your booking")
    if booking["status"] not in CANCELLABLE_STATUSES:
        raise ValueError(f"Booking cannot be cancelled (status: {booking['status']})")

    # Release slot locks
    await db[BOOKING_SLOT_LOCKS].delete_many({"booking_id": booking_id})

    await db[BOOKINGS].update_one(
        {"_id": oid},
        {"$set": {"status": "cancelled", "updated_at": utc_now()}},
    )
    booking["status"] = "cancelled"
    booking["updated_at"] = utc_now()
    return to_str_id(booking)


async def list_user_bookings(db: AsyncIOMotorDatabase, user_id: str, page=1, page_size=20):
    return await _list(db, {"user_id": user_id}, page, page_size)


async def list_all_bookings(db: AsyncIOMotorDatabase, page=1, page_size=20):
    return await _list(db, {}, page, page_size)


async def _list(db: AsyncIOMotorDatabase, filter_: dict, page: int, page_size: int):
    skip, limit = _paginate(page, page_size)
    cursor = db[BOOKINGS].find(filter_).sort("start_time", -1)
    total = await db[BOOKINGS].count_documents(filter_)
    docs = [to_str_id(d) async for d in cursor.skip(skip).limit(limit)]
    return {"items": docs, "total": total, "page": page, "page_size": limit}


def _paginate(page: int, page_size: int):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    return (page - 1) * page_size, page_size
