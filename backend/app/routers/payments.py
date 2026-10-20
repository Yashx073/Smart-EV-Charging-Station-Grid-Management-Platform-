from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import PAYMENTS, get_db
from app.dependencies import CurrentUser, get_current_user
from app.schemas import PaymentOut
from app.utils import to_str_id

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.get("", response_model=dict)
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict = {} if user.get("role") == "admin" else {"user_id": user["id"]}
    skip = (page - 1) * page_size
    if page_size < 1 or page_size > 100:
        page_size = 20
    cursor = db[PAYMENTS].find(filter_).sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[PAYMENTS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[PAYMENTS].find_one({"_id": _oid(payment_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if user.get("role") == "customer" and str(doc["user_id"]) != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your payment")
    return to_str_id(doc)
