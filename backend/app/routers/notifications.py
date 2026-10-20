from bson import ObjectId
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import NOTIFICATIONS, USERS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import NotificationCreate, NotificationOut, NotificationUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=NotificationOut, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    target_user_id = payload.user_id if user.get("role") == "admin" else user["id"]
    # Verify user exists
    target_user = await db[USERS].find_one({"_id": _oid(target_user_id)})
    if not target_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target user not found")

    now = utc_now()
    doc = payload.model_dump()
    doc["user_id"] = target_user_id
    doc["created_at"] = now
    doc["updated_at"] = now
    doc["sent_date"] = now
    res = await db[NOTIFICATIONS].insert_one(doc)
    doc["_id"] = res.inserted_id
    return to_str_id(doc)


@router.get("", response_model=dict)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    notification_type: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if user.get("role") != "admin":
        filter_["user_id"] = user["id"]
    elif user_id:
        filter_["user_id"] = user_id

    if notification_type:
        filter_["notification_type"] = notification_type
    if is_read is not None:
        filter_["is_read"] = is_read

    skip = (page - 1) * page_size
    cursor = db[NOTIFICATIONS].find(filter_).sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[NOTIFICATIONS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict[str, Any] = {"_id": _oid(notification_id)}
    if user.get("role") != "admin":
        query["user_id"] = user["id"]

    doc = await db[NOTIFICATIONS].find_one(query)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return to_str_id(doc)


@router.put("/{notification_id}", response_model=NotificationOut)
async def update_notification(
    notification_id: str = Path(...),
    payload: NotificationUpdate = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict[str, Any] = {"_id": _oid(notification_id)}
    if user.get("role") != "admin":
        query["user_id"] = user["id"]

    doc = await db[NOTIFICATIONS].find_one(query)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    data = payload.model_dump(exclude_unset=True)
    if "is_read" in data and data["is_read"]:
        data["read_status"] = "READ"
    data["updated_at"] = utc_now()

    await db[NOTIFICATIONS].update_one({"_id": _oid(notification_id)}, {"$set": data})
    updated = await db[NOTIFICATIONS].find_one({"_id": _oid(notification_id)})
    return to_str_id(updated)


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[NOTIFICATIONS].find_one({"_id": _oid(notification_id), "user_id": user["id"]})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    await db[NOTIFICATIONS].update_one(
        {"_id": _oid(notification_id)},
        {"$set": {"is_read": True, "read_status": "READ", "updated_at": utc_now()}},
    )
    doc["is_read"] = True
    doc["read_status"] = "READ"
    return to_str_id(doc)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query: dict[str, Any] = {"_id": _oid(notification_id)}
    if user.get("role") != "admin":
        query["user_id"] = user["id"]

    res = await db[NOTIFICATIONS].delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return None
