from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import USERS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import UserOut, UserRegister, UserUpdate
from app.security import hash_password
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/users", tags=["users"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc


@router.get("", response_model=dict)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") != "admin":
        # Non-admins can only see their own user profile in a list
        user_doc = await db[USERS].find_one({"_id": _oid(user["id"])})
        items = [to_str_id(user_doc)] if user_doc else []
        return {"items": items, "total": len(items), "page": 1, "page_size": page_size}

    filter_: dict[str, Any] = {}
    if role:
        filter_["role"] = role
    if status_filter:
        filter_["status"] = status_filter
    if search:
        filter_["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
        ]

    skip = (page - 1) * page_size
    cursor = db[USERS].find(filter_).sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[USERS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserRegister,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    existing = await db[USERS].find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    now = utc_now()
    doc = {
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "address": payload.address,
        "phone": payload.phone,
        "date_of_birth": payload.date_of_birth,
        "role": "customer",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    res = await db[USERS].insert_one(doc)
    doc["_id"] = res.inserted_id
    return to_str_id(doc)


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") != "admin" and user["id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    doc = await db[USERS].find_one({"_id": _oid(user_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return to_str_id(doc)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: str = Path(...),
    payload: UserUpdate = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") != "admin" and user["id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    doc = await db[USERS].find_one({"_id": _oid(user_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if "password" in data:
        data["password_hash"] = hash_password(data.pop("password"))

    # only admin can change status
    if "status" in data and user.get("role") != "admin":
        data.pop("status")

    data["updated_at"] = utc_now()
    await db[USERS].update_one({"_id": _oid(user_id)}, {"$set": data})
    updated = await db[USERS].find_one({"_id": _oid(user_id)})
    return to_str_id(updated)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user_id == user["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    res = await db[USERS].update_one(
        {"_id": _oid(user_id)},
        {"$set": {"status": "deleted", "updated_at": utc_now()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None
