from typing import Annotated, Dict

from fastapi import Cookie, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import get_db
from app.security import decode_access_token


async def get_current_user(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_db)],
    access_token: str | None = Cookie(None),
) -> Dict:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(access_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id")
    user = await db["users"].find_one({"_id": oid})
    if user is None or user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    user["id"] = str(user["_id"])
    return user


def require_role(*allowed: str):
    async def checker(user: Annotated[Dict, Depends(get_current_user)]) -> Dict:
        if user.get("role") not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return checker


CurrentUser = Dict
AdminUser = Dict
CustomerUser = Dict
