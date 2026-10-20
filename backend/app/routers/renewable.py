from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import RENEWABLE_SOURCES, SOURCES, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import RenewableSourceCreate, RenewableSourceOut, RenewableSourceUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/renewable-sources", tags=["renewable-sources"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=RenewableSourceOut, status_code=status.HTTP_201_CREATED)
async def create_renewable_source(
    payload: RenewableSourceCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    source_id = data["source_id"]

    # Verify parent SOURCE exists
    parent_source = None
    try:
        parent_source = await db[SOURCES].find_one({"_id": _oid(source_id)})
    except Exception:
        pass
    if not parent_source:
        parent_source = await db[SOURCES].find_one({"source_id": source_id})

    if not parent_source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent source with id {source_id} not found in SOURCES",
        )

    # Ensure parent source_type is RENEWABLE
    if parent_source.get("source_type", "").upper() not in {"RENEWABLE", "SOLAR", "WIND", "HYDRO"}:
        await db[SOURCES].update_one(
            {"_id": parent_source["_id"]},
            {"$set": {"source_type": "RENEWABLE", "updated_at": utc_now()}}
        )

    # Check for duplicate subtype entry
    existing = await db[RENEWABLE_SOURCES].find_one({"source_id": str(parent_source["_id"])})
    if not existing and str(parent_source["_id"]) != source_id:
        existing = await db[RENEWABLE_SOURCES].find_one({"source_id": source_id})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Renewable source specification already exists for this source")

    data["source_id"] = str(parent_source["_id"])
    if not data.get("name"):
        data["name"] = parent_source.get("name") or parent_source.get("source_name")
    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[RENEWABLE_SOURCES].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_renewable_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: Optional[str] = Query(None),
    renewable_type: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if source_id:
        filter_["source_id"] = source_id
    if renewable_type:
        filter_["renewable_type"] = renewable_type

    skip = (page - 1) * page_size
    cursor = db[RENEWABLE_SOURCES].find(filter_).skip(skip).limit(page_size)
    total = await db[RENEWABLE_SOURCES].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=RenewableSourceOut)
async def get_renewable_source(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[RENEWABLE_SOURCES].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[RENEWABLE_SOURCES].find_one({"source_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renewable source not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=RenewableSourceOut)
async def update_renewable_source(
    item_id: str = Path(...),
    payload: RenewableSourceUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[RENEWABLE_SOURCES].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renewable source not found")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[RENEWABLE_SOURCES].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[RENEWABLE_SOURCES].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_renewable_source(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[RENEWABLE_SOURCES].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Renewable source not found")
    return None
