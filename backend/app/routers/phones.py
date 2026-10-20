from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import USER_PHONES, USERS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import UserPhoneCreate, UserPhoneOut, UserPhoneUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/user-phones", tags=["user-phones"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=UserPhoneOut, status_code=status.HTTP_201_CREATED)
async def create_user_phone(
    payload: UserPhoneCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    target_user_id = data.get("user_id") if user.get("role") == "admin" and data.get("user_id") else user["id"]

    # Verify target user exists
    target_user = await db[USERS].find_one({"_id": _oid(target_user_id)})
    if not target_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    data["user_id"] = target_user_id
    phone_val = data["number"]

    # Check composite unique (user_id, number) or (user_id, phone_no)
    existing = await db[USER_PHONES].find_one(
        {"user_id": target_user_id, "$or": [{"number": phone_val}, {"phone_no": phone_val}]}
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This phone number is already registered for this user")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[USER_PHONES].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("", response_model=dict)
async def list_user_phones(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if user.get("role") != "admin":
        filter_["user_id"] = user["id"]
    elif user_id:
        filter_["user_id"] = user_id

    skip = (page - 1) * page_size
    cursor = db[USER_PHONES].find(filter_).skip(skip).limit(page_size)
    total = await db[USER_PHONES].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=UserPhoneOut)
async def get_user_phone(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[USER_PHONES].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone record not found")
    if user.get("role") != "admin" and doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your phone record")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=UserPhoneOut)
async def update_user_phone(
    item_id: str = Path(...),
    payload: UserPhoneUpdate = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[USER_PHONES].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone record not found")
    if user.get("role") != "admin" and doc.get("user_id") != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your phone record")

    data = payload.model_dump(exclude_unset=True)
    data["updated_at"] = utc_now()
    await db[USER_PHONES].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[USER_PHONES].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_phone(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict[str, Any] = {"_id": _oid(item_id)}
    if user.get("role") != "admin":
        query["user_id"] = user["id"]

    res = await db[USER_PHONES].delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone record not found")
    return None
