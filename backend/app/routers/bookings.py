from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import BOOKINGS, get_db
from app.dependencies import CurrentUser, get_current_user
from app.schemas import BookingCreate, BookingOut, BookingUpdate
from app.services.booking import cancel_booking, create_booking, list_all_bookings, list_user_bookings
from app.utils import to_str_id

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking_endpoint(
    payload: BookingCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await create_booking(db, user["id"], payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=dict)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") == "admin":
        return await list_all_bookings(db, page, page_size)
    return await list_user_bookings(db, user["id"], page, page_size)


@router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[BOOKINGS].find_one({"_id": _oid(booking_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if user.get("role") == "customer" and str(doc["user_id"]) != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your booking")
    return to_str_id(doc)


@router.post("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking_endpoint(
    booking_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await cancel_booking(db, booking_id, user["id"])
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/{booking_id}/status", response_model=BookingOut)
async def update_booking_status(
    booking_id: str = Path(...),
    payload: BookingUpdate = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    doc = await db[BOOKINGS].find_one({"_id": _oid(booking_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    await db[BOOKINGS].update_one(
        {"_id": _oid(booking_id)},
        {"$set": {"status": payload.status, "updated_at": datetime.now(timezone.utc)}},
    )
    doc["status"] = payload.status
    return to_str_id(doc)
