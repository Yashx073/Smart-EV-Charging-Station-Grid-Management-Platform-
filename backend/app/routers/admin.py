from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import ADMINS, USERS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import AdminCreate, AdminOut, AdminUpdate, UserOut, UserUpdate
from app.security import hash_password
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(tags=["admins"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


# ---------------------------------------------------------------------------
# Admin Entity CRUD (/api/admins)
# ---------------------------------------------------------------------------
@router.post("/api/admins", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
async def create_admin(
    payload: AdminCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    existing = await db[ADMINS].find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin email already registered")

    # Also ensure corresponding user account exists in USERS collection
    user_account = await db[USERS].find_one({"email": payload.email.lower()})
    now = utc_now()
    if not user_account:
        pwd = payload.password or "AdminPass123!"
        u_doc = {
            "email": payload.email.lower(),
            "password_hash": hash_password(pwd),
            "full_name": payload.full_name or payload.admin_name or "System Administrator",
            "phone": payload.phone or payload.phone_no,
            "role": "admin",
            "status": "active",
            "created_at": now,
            "updated_at": now,
        }
        res_u = await db[USERS].insert_one(u_doc)
        user_id_str = str(res_u.inserted_id)
    else:
        user_id_str = str(user_account["_id"])
        await db[USERS].update_one({"_id": user_account["_id"]}, {"$set": {"role": "admin"}})

    data = payload.model_dump()
    data.pop("password", None)
    data["email"] = data["email"].lower()
    data["user_id"] = user_id_str
    data["created_at"] = now
    data["updated_at"] = now
    data.setdefault("status", "active")

    res = await db[ADMINS].insert_one(data)
    data["_id"] = res.inserted_id
    return to_str_id(data)


@router.get("/api/admins", response_model=dict)
async def list_admins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if role:
        filter_["role"] = role
    if search:
        filter_["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"admin_name": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
        ]
    skip = (page - 1) * page_size
    cursor = db[ADMINS].find(filter_).sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[ADMINS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/api/admins/{admin_id}", response_model=AdminOut)
async def get_admin(
    admin_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[ADMINS].find_one({"_id": _oid(admin_id)})
    if not doc:
        # Check by admin_id integer / string
        doc = await db[ADMINS].find_one({"admin_id": admin_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return to_str_id(doc)


@router.put("/api/admins/{admin_id}", response_model=AdminOut)
async def update_admin(
    admin_id: str = Path(...),
    payload: AdminUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[ADMINS].find_one({"_id": _oid(admin_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    pwd = data.pop("password", None)
    if pwd and doc.get("user_id"):
        await db[USERS].update_one(
            {"_id": _oid(doc["user_id"])},
            {"$set": {"password_hash": hash_password(pwd), "updated_at": utc_now()}},
        )

    data["updated_at"] = utc_now()
    await db[ADMINS].update_one({"_id": _oid(admin_id)}, {"$set": data})
    updated = await db[ADMINS].find_one({"_id": _oid(admin_id)})
    return to_str_id(updated)


@router.delete("/api/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    res = await db[ADMINS].delete_one({"_id": _oid(admin_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return None


# ---------------------------------------------------------------------------
# Backward Compatibility for /api/admin/users
# ---------------------------------------------------------------------------
@router.get("/api/admin/users", response_model=dict)
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    skip = (page - 1) * page_size
    cursor = db[USERS].find().sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[USERS].count_documents({})
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.put("/api/admin/users/{user_id}", response_model=UserOut)
async def admin_update_user(
    user_id: str = Path(...),
    payload: UserUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[USERS].find_one({"_id": _oid(user_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    data = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if "password" in data:
        data["password_hash"] = hash_password(data.pop("password"))
    data["updated_at"] = utc_now()
    await db[USERS].update_one({"_id": _oid(user_id)}, {"$set": data})
    doc = await db[USERS].find_one({"_id": _oid(user_id)})
    return to_str_id(doc)


@router.delete("/api/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(
    user_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    if user_id == user["id"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    res = await db[USERS].update_one(
        {"_id": _oid(user_id)}, {"$set": {"status": "deleted", "updated_at": utc_now()}}
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None
