from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import CHARGING_SESSIONS, get_db
from app.dependencies import CurrentUser, get_current_user
from app.schemas import SessionEnd, SessionOut, SessionStart
from app.services.session import end_session, list_all_sessions, list_user_sessions, start_session
from app.utils import to_str_id

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
@router.post("/start", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def start_session_endpoint(
    payload: SessionStart,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await start_session(db, user["id"], payload.model_dump())
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/{session_id}/end", response_model=SessionOut)
async def end_session_endpoint(
    session_id: str = Path(...),
    payload: SessionEnd = ...,  # type: ignore[valid-type]
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    try:
        return await end_session(db, session_id, user["id"], payload.model_dump())
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=dict)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if user.get("role") == "admin":
        return await list_all_sessions(db, page, page_size)
    return await list_user_sessions(db, user["id"], page, page_size)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CHARGING_SESSIONS].find_one({"_id": _oid(session_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if user.get("role") == "customer" and str(doc["user_id"]) != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return to_str_id(doc)
