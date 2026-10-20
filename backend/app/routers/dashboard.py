from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import (
    BOOKINGS,
    CHARGING_PORTS,
    CHARGING_SESSIONS,
    CHARGING_STATIONS,
    MAINTENANCE,
    PAYMENTS,
    USERS,
    get_db,
)
from app.dependencies import CurrentUser, get_current_user
from app.schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _start_of_day(d: datetime) -> datetime:
    return d.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("/stats", response_model=DashboardStats)
async def stats(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    total_users = await db[USERS].count_documents({})
    total_stations = await db[CHARGING_STATIONS].count_documents({})
    total_ports = await db[CHARGING_PORTS].count_documents({})
    total_bookings = await db[BOOKINGS].count_documents({})
    total_sessions = await db[CHARGING_SESSIONS].count_documents({})
    rev = await db[PAYMENTS].aggregate(
        [{"$group": {"_id": None, "total": {"$sum": "$amount"}}}]
    ).to_list(1)
    total_revenue = rev[0]["total"] if rev else 0
    total_maintenance = await db[MAINTENANCE].count_documents({})
    return DashboardStats(
        total_users=total_users,
        total_stations=total_stations,
        total_ports=total_ports,
        total_bookings=total_bookings,
        total_sessions=total_sessions,
        total_revenue=total_revenue,
        total_maintenance=total_maintenance,
    )


@router.get("/trends", response_model=dict)
async def trends(
    days: int = Query(7, ge=1, le=30),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    from_date = _start_of_day(now - timedelta(days=days - 1))

    async def trend(col, date_field, value_field=None):
        pipeline = [
            {"$match": {date_field: {"$gte": from_date}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": f"${date_field}"}},
                    "count": {"$sum": 1},
                    "sum": {"$sum": value_field} if value_field else {"$sum": 0},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        return await col.aggregate(pipeline).to_list(None)

    bookings = await trend(db[BOOKINGS], "start_time")
    sessions = await trend(db[CHARGING_SESSIONS], "started_at")
    revenue = await trend(db[PAYMENTS], "created_at")

    return {
        "booking_trend": [{"date": b["_id"], "count": b["count"]} for b in bookings],
        "revenue_trend": [{"date": r["_id"], "amount": r["sum"]} for r in revenue],
        "energy_trend": [{"date": s["_id"], "kwh": s["sum"]} for s in sessions],
    }
