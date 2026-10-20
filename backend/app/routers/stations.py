from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import CHARGING_STATIONS, GRIDS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import StationCreate, StationOut, StationUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/stations", tags=["stations"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=StationOut, status_code=status.HTTP_201_CREATED)
async def create_station(
    payload: StationCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    code = data["station_code"]

    existing = await db[CHARGING_STATIONS].find_one({"station_code": code})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Station code already exists")

    if data.get("grid_id"):
        grid = await db[GRIDS].find_one({"_id": _oid(data["grid_id"])})
        if not grid:
            grid = await db[GRIDS].find_one({"grid_id": data["grid_id"]})
        if not grid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced grid not found")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[CHARGING_STATIONS].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_stations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    grid_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    city: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if grid_id:
        filter_["grid_id"] = grid_id
    if status_filter:
        filter_["status"] = status_filter
    if city:
        filter_["city"] = city
    if search:
        filter_["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"station_name": {"$regex": search, "$options": "i"}},
            {"station_code": {"$regex": search, "$options": "i"}},
            {"city": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * page_size
    cursor = db[CHARGING_STATIONS].find(filter_).skip(skip).limit(page_size)
    total = await db[CHARGING_STATIONS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=StationOut)
async def get_station(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CHARGING_STATIONS].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[CHARGING_STATIONS].find_one({"station_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=StationOut)
async def update_station(
    item_id: str = Path(...),
    payload: StationUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CHARGING_STATIONS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    data = payload.model_dump(exclude_unset=True)
    if "grid_id" in data and data["grid_id"]:
        grid = await db[GRIDS].find_one({"_id": _oid(data["grid_id"])})
        if not grid:
            grid = await db[GRIDS].find_one({"grid_id": data["grid_id"]})
        if not grid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced grid not found")

    data["updated_at"] = utc_now()
    await db[CHARGING_STATIONS].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[CHARGING_STATIONS].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[CHARGING_STATIONS].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
    return None
