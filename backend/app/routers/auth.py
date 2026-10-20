from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.database import USERS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.security import create_access_token, hash_password, verify_password
from app.schemas import TokenOut, UserLogin, UserOut, UserRegister
from app.utils import to_str_id

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_same_site,
        path="/",
        max_age=60 * 60 * 24 * 7,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing = await db[USERS].find_one({"email": payload.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    doc = {
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name,
        "phone": payload.phone,
        "role": "customer",
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    }
    res = await db[USERS].insert_one(doc)
    doc["_id"] = res.inserted_id
    user = UserOut(**to_str_id(doc))
    token = create_access_token({"sub": user.id, "role": user.role})
    _set_auth_cookie(response, token)
    return user


@router.post("/login", response_model=TokenOut)
async def login(payload: UserLogin, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db[USERS].find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not active")
    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    _set_auth_cookie(response, token)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser = Depends(get_current_user)):
    return user


@router.get("/admin/users", response_model=dict)
async def admin_list_users(
    page: int = 1,
    page_size: int = 20,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    skip = (page - 1) * page_size
    cursor = db[USERS].find().sort("created_at", -1).skip(skip).limit(page_size)
    total = await db[USERS].count_documents({})
    items = []
    async for d in cursor:
        items.append(to_str_id(d))
    return {"items": items, "total": total, "page": page, "page_size": page_size}
