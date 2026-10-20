from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import NON_RENEWABLE_SOURCES, SOURCES, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import NonRenewableSourceCreate, NonRenewableSourceOut, NonRenewableSourceUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/non-renewable-sources", tags=["non-renewable-sources"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=NonRenewableSourceOut, status_code=status.HTTP_201_CREATED)
async def create_non_renewable_source(
    payload: NonRenewableSourceCreate,
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

    # Ensure parent source_type is NON_RENEWABLE
    if parent_source.get("source_type", "").upper() not in {"NON_RENEWABLE", "GAS", "COAL", "DIESEL"}:
        await db[SOURCES].update_one(
            {"_id": parent_source["_id"]},
            {"$set": {"source_type": "NON_RENEWABLE", "updated_at": utc_now()}}
        )

    # Check for duplicate subtype entry
    existing = await db[NON_RENEWABLE_SOURCES].find_one({"source_id": str(parent_source["_id"])})
    if not existing and str(parent_source["_id"]) != source_id:
        existing = await db[NON_RENEWABLE_SOURCES].find_one({"source_id": source_id})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Non-renewable source specification already exists for this source")

    data["source_id"] = str(parent_source["_id"])
    if not data.get("name"):
        data["name"] = parent_source.get("name") or parent_source.get("source_name")
    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[NON_RENEWABLE_SOURCES].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_non_renewable_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source_id: Optional[str] = Query(None),
    fuel_type: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if source_id:
        filter_["source_id"] = source_id
    if fuel_type:
        filter_["fuel_type"] = fuel_type

    skip = (page - 1) * page_size
    cursor = db[NON_RENEWABLE_SOURCES].find(filter_).skip(skip).limit(page_size)
    total = await db[NON_RENEWABLE_SOURCES].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=NonRenewableSourceOut)
async def get_non_renewable_source(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[NON_RENEWABLE_SOURCES].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[NON_RENEWABLE_SOURCES].find_one({"source_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non-renewable source not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=NonRenewableSourceOut)
async def update_non_renewable_source(
    item_id: str = Path(...),
    payload: NonRenewableSourceUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[NON_RENEWABLE_SOURCES].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non-renewable source not found")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[NON_RENEWABLE_SOURCES].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[NON_RENEWABLE_SOURCES].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_non_renewable_source(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[NON_RENEWABLE_SOURCES].delete_one({"_id": _oid(item_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Non-renewable source not found")
    return None
