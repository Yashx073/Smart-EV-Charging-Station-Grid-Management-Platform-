from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import BATTERY_STATUS, EVS, USERS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import EVCreate, EVOut, EVUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/evs", tags=["evs"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=EVOut, status_code=status.HTTP_201_CREATED)
async def create_ev(
    payload: EVCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    target_owner = data.get("owner_id") or data.get("user_id")
    if user.get("role") != "admin" or not target_owner:
        target_owner = user["id"]

    # Verify owner exists
    owner_doc = await db[USERS].find_one({"_id": _oid(target_owner)})
    if not owner_doc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EV owner user not found")

    data["owner_id"] = target_owner
    data["user_id"] = target_owner

    reg_num = data["registration_number"]
    existing = await db[EVS].find_one(
        {"$or": [{"registration_number": reg_num}, {"vehicle_number": reg_num}]}
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="EV with this registration number already exists")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[EVS].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_evs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    owner_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if user.get("role") != "admin":
        filter_["$or"] = [{"owner_id": user["id"]}, {"user_id": user["id"]}]
    else:
        target = owner_id or user_id
        if target:
            filter_["$or"] = [{"owner_id": target}, {"user_id": target}]

    if search:
        search_filter = [
            {"model": {"$regex": search, "$options": "i"}},
            {"registration_number": {"$regex": search, "$options": "i"}},
            {"vehicle_number": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
        ]
        if "$or" in filter_:
            filter_["$and"] = [{"$or": filter_.pop("$or")}, {"$or": search_filter}]
        else:
            filter_["$or"] = search_filter

    skip = (page - 1) * page_size
    cursor = db[EVS].find(filter_).sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[EVS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=EVOut)
async def get_ev(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[EVS].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[EVS].find_one({"ev_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EV not found")

    if user.get("role") != "admin" and doc.get("owner_id") != user["id"] and doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your EV")

    return to_str_id(doc)


@router.put("/{item_id}", response_model=EVOut)
async def update_ev(
    item_id: str = Path(...),
    payload: EVUpdate = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[EVS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EV not found")

    if user.get("role") != "admin" and doc.get("owner_id") != user["id"] and doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your EV")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[EVS].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[EVS].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ev(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[EVS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="EV not found")

    await db[EVS].delete_one({"_id": _oid(item_id)})
    return None
