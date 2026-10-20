from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import TARIFFS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import TariffCreate, TariffOut, TariffUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/tariffs", tags=["tariffs"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=TariffOut, status_code=status.HTTP_201_CREATED)
async def create_tariff(
    payload: TariffCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    name = data["name"]

    existing = await db[TARIFFS].find_one({"name": name})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tariff with this name already exists")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[TARIFFS].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_tariffs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if is_active is not None:
        filter_["is_active"] = is_active
    if search:
        filter_["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"tariff_name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * page_size
    cursor = db[TARIFFS].find(filter_).sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[TARIFFS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=TariffOut)
async def get_tariff(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[TARIFFS].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[TARIFFS].find_one({"tariff_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=TariffOut)
async def update_tariff(
    item_id: str = Path(...),
    payload: TariffUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[TARIFFS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[TARIFFS].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[TARIFFS].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tariff(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[TARIFFS].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")
    return None
