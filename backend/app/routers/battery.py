from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import BATTERY_STATUS, EVS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import BatteryStatusCreate, BatteryStatusOut, BatteryStatusUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/battery-status", tags=["battery-status"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=BatteryStatusOut, status_code=status.HTTP_201_CREATED)
async def create_battery_status(
    payload: BatteryStatusCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    ev_id = data["ev_id"]

    # Verify EV exists
    ev_query: dict[str, Any] = {"_id": _oid(ev_id)}
    if user.get("role") != "admin":
        ev_query["owner_id"] = user["id"]

    ev = await db[EVS].find_one(ev_query)
    if not ev:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EV not found or not owned by you")

    # Check 1-to-1 uniqueness
    existing = await db[BATTERY_STATUS].find_one({"ev_id": ev_id})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Battery status record already exists for this EV")

    now = utc_now()
    data["recorded_at"] = now
    data["last_updated"] = now
    data["created_at"] = now
    data["updated_at"] = now
    res = await db[BATTERY_STATUS].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_battery_status(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ev_id: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if user.get("role") != "admin":
        # Find all EVs owned by user
        user_evs = await db[EVS].find({"owner_id": user["id"]}).to_list(length=100)
        ev_ids = [str(e["_id"]) for e in user_evs]
        if ev_id:
            if ev_id not in ev_ids:
                return {"items": [], "total": 0, "page": page, "page_size": page_size}
            filter_["ev_id"] = ev_id
        else:
            filter_["ev_id"] = {"$in": ev_ids}
    elif ev_id:
        filter_["ev_id"] = ev_id

    skip = (page - 1) * page_size
    cursor = db[BATTERY_STATUS].find(filter_).sort("recorded_at", -1).skip(skip).limit(page_size)
    total = await db[BATTERY_STATUS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=BatteryStatusOut)
async def get_battery_status(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[BATTERY_STATUS].find_one({"_id": _oid(item_id)})
    if not doc:
        # Also check by ev_id
        doc = await db[BATTERY_STATUS].find_one({"ev_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battery status not found")

    if user.get("role") != "admin":
        ev = await db[EVS].find_one({"_id": _oid(doc["ev_id"]), "owner_id": user["id"]})
        if not ev:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your EV")

    return to_str_id(doc)


@router.put("/{item_id}", response_model=BatteryStatusOut)
async def update_battery_status(
    item_id: str = Path(...),
    payload: BatteryStatusUpdate = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[BATTERY_STATUS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battery status not found")

    if user.get("role") != "admin":
        ev = await db[EVS].find_one({"_id": _oid(doc["ev_id"]), "owner_id": user["id"]})
        if not ev:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your EV")

    data = payload.model_dump(exclude_unset=True)
    now = utc_now()
    data["last_updated"] = now
    data["updated_at"] = now
    await db[BATTERY_STATUS].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[BATTERY_STATUS].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_battery_status(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[BATTERY_STATUS].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Battery status not found")
    return None
