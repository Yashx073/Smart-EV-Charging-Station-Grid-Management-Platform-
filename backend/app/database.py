from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import CollectionInvalid, OperationFailure

from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

# Collection names — All 22 Smart EV Entities + concurrency lock collection
USERS = "users"
ADMINS = "admins"
TARIFFS = "tariffs"
SOURCES = "sources"
CHARGING_STATIONS = "charging_stations"
EVS = "evs"
USER_PHONES = "user_phones"
GRIDS = "grids"
CHARGING_PORTS = "charging_ports"
AC_PORTS = "ac_ports"
DC_FAST_PORTS = "dc_fast_ports"
BOOKINGS = "bookings"
CHARGING_SESSIONS = "charging_sessions"
PAYMENTS = "payments"
SCHEDULES = "schedules"
MAINTENANCE = "maintenance"
NOTIFICATIONS = "notifications"
BATTERY_STATUS = "battery_status"
RENEWABLE_SOURCES = "renewable_sources"
NON_RENEWABLE_SOURCES = "non_renewable_sources"
PREVENTIVE_MAINTENANCE = "preventive_maintenance"
CORRECTIVE_MAINTENANCE = "corrective_maintenance"
BOOKING_SLOT_LOCKS = "booking_slot_locks"

ALL_COLLECTIONS = [
    USERS,
    ADMINS,
    TARIFFS,
    SOURCES,
    CHARGING_STATIONS,
    EVS,
    USER_PHONES,
    GRIDS,
    CHARGING_PORTS,
    AC_PORTS,
    DC_FAST_PORTS,
    BOOKINGS,
    CHARGING_SESSIONS,
    PAYMENTS,
    SCHEDULES,
    MAINTENANCE,
    NOTIFICATIONS,
    BATTERY_STATUS,
    RENEWABLE_SOURCES,
    NON_RENEWABLE_SOURCES,
    PREVENTIVE_MAINTENANCE,
    CORRECTIVE_MAINTENANCE,
]


async def connect_db() -> AsyncIOMotorDatabase:
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
        _db = _client[settings.mongodb_db]
        await _db.command("ping")
    return _db


async def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        await connect_db()
    return _db  # type: ignore[return-value]


async def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


async def _safe_index(collection, keys, **kwargs):
    try:
        await collection.create_index(keys, **kwargs)
    except OperationFailure:
        # If options conflict with an existing index on same field, keep existing or retry
        try:
            if "sparse" in kwargs:
                kwargs.pop("sparse")
                await collection.create_index(keys, **kwargs)
        except Exception:
            pass
    except Exception:
        pass


async def init_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create indexes and lightweight schema validation for all 22 entities. Idempotent."""
    for col in ALL_COLLECTIONS + [BOOKING_SLOT_LOCKS]:
        try:
            await db.create_collection(col)
        except CollectionInvalid:
            pass

    # 1. USERS
    await _safe_index(db[USERS], "email", unique=True)
    await _safe_index(db[USERS], "role")
    await _safe_index(db[USERS], "status")
    await _safe_index(db[USERS], "user_id", unique=True, sparse=True)

    # 2. ADMINS
    await _safe_index(db[ADMINS], "email", unique=True)
    await _safe_index(db[ADMINS], "user_id")
    await _safe_index(db[ADMINS], "admin_id", unique=True, sparse=True)

    # 3. TARIFFS
    await _safe_index(db[TARIFFS], "name", unique=True)
    await _safe_index(db[TARIFFS], "tariff_name", sparse=True)
    await _safe_index(db[TARIFFS], "tariff_id", unique=True, sparse=True)
    await _safe_index(db[TARIFFS], "is_active")

    # 4. SOURCES
    await _safe_index(db[SOURCES], "name", unique=True, sparse=True)
    await _safe_index(db[SOURCES], "source_name", sparse=True)
    await _safe_index(db[SOURCES], "source_id", unique=True, sparse=True)
    await _safe_index(db[SOURCES], "source_type")
    await _safe_index(db[SOURCES], "status")

    # 5. CHARGING_STATIONS
    await _safe_index(db[CHARGING_STATIONS], "station_code", unique=True)
    await _safe_index(db[CHARGING_STATIONS], "station_id", unique=True, sparse=True)
    await _safe_index(db[CHARGING_STATIONS], "grid_id")
    await _safe_index(db[CHARGING_STATIONS], "status")

    # 6. EVS
    await _safe_index(db[EVS], "registration_number", unique=True)
    await _safe_index(db[EVS], "vehicle_number", unique=True, sparse=True)
    await _safe_index(db[EVS], "ev_id", unique=True, sparse=True)
    await _safe_index(db[EVS], "owner_id")
    await _safe_index(db[EVS], "user_id")

    # 7. USER_PHONES
    await _safe_index(db[USER_PHONES], [("user_id", ASCENDING), ("number", ASCENDING)], unique=True)
    await _safe_index(db[USER_PHONES], [("user_id", ASCENDING), ("phone_no", ASCENDING)], unique=True, sparse=True)
    await _safe_index(db[USER_PHONES], "user_id")

    # 8. GRIDS
    await _safe_index(db[GRIDS], "name", unique=True)
    await _safe_index(db[GRIDS], "grid_name", sparse=True)
    await _safe_index(db[GRIDS], "grid_id", unique=True, sparse=True)
    await _safe_index(db[GRIDS], "source_id")

    # 9. CHARGING_PORTS
    await _safe_index(db[CHARGING_PORTS], [("station_id", ASCENDING), ("port_number", ASCENDING)], unique=True)
    await _safe_index(db[CHARGING_PORTS], "port_id", unique=True, sparse=True)
    await _safe_index(db[CHARGING_PORTS], "station_id")
    await _safe_index(db[CHARGING_PORTS], "tariff_id")
    await _safe_index(db[CHARGING_PORTS], "status")

    # 10. AC_PORTS
    await _safe_index(db[AC_PORTS], [("station_id", ASCENDING), ("port_number", ASCENDING)], unique=True)
    await _safe_index(db[AC_PORTS], "port_id", unique=True, sparse=True)
    await _safe_index(db[AC_PORTS], "station_id")

    # 11. DC_FAST_PORTS
    await _safe_index(db[DC_FAST_PORTS], [("station_id", ASCENDING), ("port_number", ASCENDING)], unique=True)
    await _safe_index(db[DC_FAST_PORTS], "port_id", unique=True, sparse=True)
    await _safe_index(db[DC_FAST_PORTS], "station_id")

    # 12. BOOKINGS
    await _safe_index(db[BOOKINGS], "booking_id", unique=True, sparse=True)
    await _safe_index(db[BOOKINGS], "user_id")
    await _safe_index(db[BOOKINGS], "station_id")
    await _safe_index(db[BOOKINGS], "port_id")
    await _safe_index(db[BOOKINGS], "status")
    await _safe_index(db[BOOKINGS], "start_time")
    await _safe_index(db[BOOKINGS], "end_time")

    # 13. CHARGING_SESSIONS
    await _safe_index(db[CHARGING_SESSIONS], "session_id", unique=True, sparse=True)
    await _safe_index(db[CHARGING_SESSIONS], "booking_id", unique=True, sparse=True)
    await _safe_index(db[CHARGING_SESSIONS], "port_id")
    await _safe_index(db[CHARGING_SESSIONS], "user_id")
    await _safe_index(db[CHARGING_SESSIONS], "status")
    await _safe_index(db[CHARGING_SESSIONS], "started_at")

    # 14. PAYMENTS
    await _safe_index(db[PAYMENTS], "payment_id", unique=True, sparse=True)
    await _safe_index(db[PAYMENTS], "session_id", unique=True, sparse=True)
    await _safe_index(db[PAYMENTS], "transaction_reference", unique=True)
    await _safe_index(db[PAYMENTS], "status")
    await _safe_index(db[PAYMENTS], "user_id")

    # 15. SCHEDULES
    await _safe_index(db[SCHEDULES], "schedule_id", unique=True, sparse=True)
    await _safe_index(db[SCHEDULES], [("port_id", ASCENDING), ("start_time", ASCENDING)])
    await _safe_index(db[SCHEDULES], [("station_id", ASCENDING), ("start_time", ASCENDING)])
    await _safe_index(db[SCHEDULES], "station_id")

    # 16. MAINTENANCE
    await _safe_index(db[MAINTENANCE], "maintenance_id", unique=True, sparse=True)
    await _safe_index(db[MAINTENANCE], "station_id")
    await _safe_index(db[MAINTENANCE], "port_id")
    await _safe_index(db[MAINTENANCE], "admin_id")
    await _safe_index(db[MAINTENANCE], "status")

    # 17. NOTIFICATIONS
    await _safe_index(db[NOTIFICATIONS], "notification_id", unique=True, sparse=True)
    await _safe_index(db[NOTIFICATIONS], "user_id")
    await _safe_index(db[NOTIFICATIONS], "created_at")
    await _safe_index(db[NOTIFICATIONS], "is_read")

    # 18. BATTERY_STATUS
    await _safe_index(db[BATTERY_STATUS], "battery_status_id", unique=True, sparse=True)
    await _safe_index(db[BATTERY_STATUS], "ev_id")
    await _safe_index(db[BATTERY_STATUS], "recorded_at")

    # 19. RENEWABLE_SOURCES
    await _safe_index(db[RENEWABLE_SOURCES], "source_id", unique=True, sparse=True)
    await _safe_index(db[RENEWABLE_SOURCES], "name", unique=True, sparse=True)

    # 20. NON_RENEWABLE_SOURCES
    await _safe_index(db[NON_RENEWABLE_SOURCES], "source_id", unique=True, sparse=True)
    await _safe_index(db[NON_RENEWABLE_SOURCES], "name", unique=True, sparse=True)

    # 21. PREVENTIVE_MAINTENANCE
    await _safe_index(db[PREVENTIVE_MAINTENANCE], "maintenance_id", unique=True, sparse=True)
    await _safe_index(db[PREVENTIVE_MAINTENANCE], "station_id")

    # 22. CORRECTIVE_MAINTENANCE
    await _safe_index(db[CORRECTIVE_MAINTENANCE], "maintenance_id", unique=True, sparse=True)
    await _safe_index(db[CORRECTIVE_MAINTENANCE], "station_id")

    # Slot locks: one document per (port_id, slot_start). Unique index prevents
    # two concurrent bookings from reserving the same 30-minute slot on a port.
    await _safe_index(
        db[BOOKING_SLOT_LOCKS],
        [("port_id", ASCENDING), ("slot_start", ASCENDING)],
        unique=True,
    )
    await _safe_index(db[BOOKING_SLOT_LOCKS], "expires_at", expireAfterSeconds=0)

    # Schema validation (lightweight) for key collections.
    await _add_validator(db, USERS, {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["email", "password_hash"],
            "properties": {
                "role": {"type": "string"},
                "status": {"type": "string"},
            },
        }
    })
    await _add_validator(db, BOOKINGS, {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["user_id", "station_id", "start_time", "end_time", "status"],
            "properties": {
                "status": {"type": "string"},
            },
        }
    })
    await _add_validator(db, CHARGING_SESSIONS, {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["port_id", "status"],
            "properties": {
                "status": {"type": "string"},
            },
        }
    })
    await _add_validator(db, PAYMENTS, {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["session_id", "amount", "transaction_reference", "status"],
            "properties": {
                "status": {"type": "string"},
            },
        }
    })


async def _add_validator(db: AsyncIOMotorDatabase, collection: str, validator: dict) -> None:
    try:
        await db.create_collection(collection)
    except CollectionInvalid:
        pass
    try:
        await db.command("collMod", collection, validator=validator)
    except Exception:
        # collMod may fail on some MongoDB configurations; indexes still apply.
        pass
