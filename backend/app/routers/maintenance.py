from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import ADMINS, CHARGING_PORTS, CHARGING_STATIONS, MAINTENANCE, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import MaintenanceCreate, MaintenanceOut, MaintenanceUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    payload: MaintenanceCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    station_id = data.get("station_id")

    # If station_id provided, verify station exists
    if station_id:
        stn = await db[CHARGING_STATIONS].find_one({"_id": _oid(station_id)})
        if not stn:
            stn = await db[CHARGING_STATIONS].find_one({"station_id": station_id})
        if not stn:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Charging station not found")

    # If admin_id supplied, check it
    if data.get("admin_id"):
        admin_doc = await db[ADMINS].find_one({"_id": _oid(data["admin_id"])})
        if not admin_doc:
            admin_doc = await db[ADMINS].find_one({"admin_id": data["admin_id"]})
        if not admin_doc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced administrator not found")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[MAINTENANCE].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_maintenance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: Optional[str] = Query(None),
    port_id: Optional[str] = Query(None),
    admin_id: Optional[str] = Query(None),
    maintenance_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if station_id:
        filter_["station_id"] = station_id
    if port_id:
        filter_["port_id"] = port_id
    if admin_id:
        filter_["admin_id"] = admin_id
    if maintenance_type:
        filter_["maintenance_type"] = maintenance_type.upper()
    if status_filter:
        filter_["status"] = status_filter

    skip = (page - 1) * page_size
    cursor = db[MAINTENANCE].find(filter_).sort("scheduled_date", -1).skip(skip).limit(page_size)
    total = await db[MAINTENANCE].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=MaintenanceOut)
async def get_maintenance(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[MAINTENANCE].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[MAINTENANCE].find_one({"maintenance_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=MaintenanceOut)
async def update_maintenance(
    item_id: str = Path(...),
    payload: MaintenanceUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[MAINTENANCE].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[MAINTENANCE].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[MAINTENANCE].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_maintenance(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[MAINTENANCE].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found")
    return None
