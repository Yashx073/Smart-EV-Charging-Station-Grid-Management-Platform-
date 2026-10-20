from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import MAINTENANCE, CORRECTIVE_MAINTENANCE, CHARGING_STATIONS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import CorrectiveMaintenanceCreate, CorrectiveMaintenanceOut, CorrectiveMaintenanceUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/corrective-maintenance", tags=["corrective-maintenance"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=CorrectiveMaintenanceOut, status_code=status.HTTP_201_CREATED)
async def create_corrective_maintenance(
    payload: CorrectiveMaintenanceCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    maintenance_id = data["maintenance_id"]

    # Verify parent MAINTENANCE exists
    parent_maint = None
    try:
        parent_maint = await db[MAINTENANCE].find_one({"_id": _oid(maintenance_id)})
    except Exception:
        pass
    if not parent_maint:
        parent_maint = await db[MAINTENANCE].find_one({"maintenance_id": maintenance_id})

    if not parent_maint:
        # Check if station_id exists; if so, create parent maintenance record automatically
        station_id = data.get("station_id")
        if station_id:
            try:
                stn = await db[CHARGING_STATIONS].find_one({"_id": _oid(station_id)})
            except Exception:
                stn = None
            if not stn:
                stn = await db[CHARGING_STATIONS].find_one({"station_id": station_id})
            if stn:
                now_dt = utc_now()
                m_doc = {
                    "station_id": str(stn["_id"]),
                    "port_id": data.get("port_id"),
                    "maintenance_type": "CORRECTIVE",
                    "title": data.get("fault_title") or "Corrective Repair",
                    "description": data.get("fault_description") or data.get("description") or "Corrective action required",
                    "scheduled_date": now_dt,
                    "cost": 0.0,
                    "status": "planned",
                    "created_at": now_dt,
                    "updated_at": now_dt,
                }
                res_m = await db[MAINTENANCE].insert_one(m_doc)
                parent_maint = m_doc
                parent_maint["_id"] = res_m.inserted_id

    if not parent_maint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent maintenance record with id {maintenance_id} not found",
        )

    # Check for duplicate
    existing = await db[CORRECTIVE_MAINTENANCE].find_one({"maintenance_id": str(parent_maint["_id"])})
    if not existing and str(parent_maint["_id"]) != maintenance_id:
        existing = await db[CORRECTIVE_MAINTENANCE].find_one({"maintenance_id": maintenance_id})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrective maintenance details already exist for this record")

    data["maintenance_id"] = str(parent_maint["_id"])
    data["station_id"] = parent_maint.get("station_id") or data.get("station_id")
    data["port_id"] = parent_maint.get("port_id") or data.get("port_id")
    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now
    if not data.get("reported_date"):
        data["reported_date"] = now

    res = await db[CORRECTIVE_MAINTENANCE].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_corrective_maintenance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    maintenance_id: Optional[str] = Query(None),
    station_id: Optional[str] = Query(None),
    port_id: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if maintenance_id:
        filter_["maintenance_id"] = maintenance_id
    if station_id:
        filter_["station_id"] = station_id
    if port_id:
        filter_["port_id"] = port_id

    skip = (page - 1) * page_size
    cursor = db[CORRECTIVE_MAINTENANCE].find(filter_).skip(skip).limit(page_size)
    total = await db[CORRECTIVE_MAINTENANCE].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=CorrectiveMaintenanceOut)
async def get_corrective_maintenance(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CORRECTIVE_MAINTENANCE].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[CORRECTIVE_MAINTENANCE].find_one({"maintenance_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective maintenance record not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=CorrectiveMaintenanceOut)
async def update_corrective_maintenance(
    item_id: str = Path(...),
    payload: CorrectiveMaintenanceUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CORRECTIVE_MAINTENANCE].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective maintenance record not found")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[CORRECTIVE_MAINTENANCE].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[CORRECTIVE_MAINTENANCE].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_corrective_maintenance(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[CORRECTIVE_MAINTENANCE].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrective maintenance record not found")
    return None
