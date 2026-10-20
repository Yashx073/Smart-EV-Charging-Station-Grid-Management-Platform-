from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import GRIDS, SOURCES, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import GridCreate, GridOut, GridUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/grids", tags=["grids"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=GridOut, status_code=status.HTTP_201_CREATED)
async def create_grid(
    payload: GridCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    source_id = data.get("source_id")
    if source_id:
        src = await db[SOURCES].find_one({"_id": _oid(source_id)})
        if not src:
            src = await db[SOURCES].find_one({"source_id": source_id})
        if not src:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced energy source not found")

    existing = await db[GRIDS].find_one({"name": data["name"]})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Grid with this name already exists")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[GRIDS].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_grids(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if source_id:
        filter_["source_id"] = source_id
    if status_filter:
        filter_["status"] = status_filter
    if search:
        filter_["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"grid_name": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * page_size
    cursor = db[GRIDS].find(filter_).skip(skip).limit(page_size)
    total = await db[GRIDS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=GridOut)
async def get_grid(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[GRIDS].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[GRIDS].find_one({"grid_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grid not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=GridOut)
async def update_grid(
    item_id: str = Path(...),
    payload: GridUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[GRIDS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grid not found")

    data = payload.model_dump(exclude_unset=True)
    if "source_id" in data and data["source_id"]:
        src = await db[SOURCES].find_one({"_id": _oid(data["source_id"])})
        if not src:
            src = await db[SOURCES].find_one({"source_id": data["source_id"]})
        if not src:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced energy source not found")

    data["updated_at"] = utc_now()
    await db[GRIDS].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[GRIDS].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grid(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[GRIDS].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grid not found")
    return None
