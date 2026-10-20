from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import CHARGING_STATIONS, SCHEDULES, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import ScheduleCreate, ScheduleOut, ScheduleUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ScheduleCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    station_id = data["station_id"]

    # Verify station exists
    stn = await db[CHARGING_STATIONS].find_one({"_id": _oid(station_id)})
    if not stn:
        stn = await db[CHARGING_STATIONS].find_one({"station_id": station_id})
    if not stn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Charging station not found")

    if data["end_time"] <= data["start_time"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[SCHEDULES].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: Optional[str] = Query(None),
    port_id: Optional[str] = Query(None),
    schedule_date: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if station_id:
        filter_["station_id"] = station_id
    if port_id:
        filter_["port_id"] = port_id
    if schedule_date:
        filter_["schedule_date"] = schedule_date

    skip = (page - 1) * page_size
    cursor = db[SCHEDULES].find(filter_).sort("start_time", 1).skip(skip).limit(page_size)
    total = await db[SCHEDULES].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=ScheduleOut)
async def get_schedule(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[SCHEDULES].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=ScheduleOut)
async def update_schedule(
    item_id: str = Path(...),
    payload: ScheduleUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[SCHEDULES].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    data = payload.model_dump(exclude_unset=True)
    start_time = data.get("start_time", doc.get("start_time"))
    end_time = data.get("end_time", doc.get("end_time"))
    if start_time and end_time and end_time <= start_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time must be after start_time")

    data["updated_at"] = utc_now()
    await db[SCHEDULES].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[SCHEDULES].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[SCHEDULES].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    return None
