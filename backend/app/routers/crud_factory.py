from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.repository import BaseRepository


def crud_router(
    *,
    collection: str,
    create_schema: type,
    update_schema: type,
    out_schema: type,
    prefix: str,
    tags: list[str],
    customer_create: bool = True,
    owner_field: str = "owner_id",
    admin_delete: bool = True,
    customer_owns: bool = True,
    require_admin_read: bool = False,
    require_admin_create: bool = False,
    require_admin_update: bool = False,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)

    async def get_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> BaseRepository:
        return BaseRepository(db, collection)

    @router.post("", response_model=out_schema, status_code=status.HTTP_201_CREATED)
    async def create_item(
        payload: create_schema,
        user: CurrentUser = Depends(get_current_user),
        r: BaseRepository = Depends(get_repo),
    ):
        if require_admin_create and user.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
        data = payload.model_dump()
        if customer_create and user.get("role") == "customer":
            data[owner_field] = user["id"]
        return await r.create(data)

    @router.get("", response_model=dict)
    async def list_items(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        station_id: Optional[str] = Query(None),
        user_id: Optional[str] = Query(None),
        port_id: Optional[str] = Query(None),
        ev_id: Optional[str] = Query(None),
        source_id: Optional[str] = Query(None),
        maintenance_id: Optional[str] = Query(None),
        status_filter: Optional[str] = Query(None, alias="status"),
        search: Optional[str] = Query(None),
        user: CurrentUser = Depends(get_current_user),
        r: BaseRepository = Depends(get_repo),
    ):
        if require_admin_read and user.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
        filter_: dict[str, Any] = {}
        if user.get("role") == "customer" and customer_owns:
            filter_[owner_field] = user["id"]
        elif user_id:
            filter_["user_id"] = user_id
        if station_id:
            filter_["station_id"] = station_id
        if port_id:
            filter_["port_id"] = port_id
        if ev_id:
            filter_["ev_id"] = ev_id
        if source_id:
            filter_["source_id"] = source_id
        if maintenance_id:
            filter_["maintenance_id"] = maintenance_id
        if status_filter:
            filter_["$or"] = [{"status": status_filter}, {"availability_status": status_filter}]
        if search:
            filter_["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"station_name": {"$regex": search, "$options": "i"}},
                {"title": {"$regex": search, "$options": "i"}},
                {"model": {"$regex": search, "$options": "i"}},
                {"registration_number": {"$regex": search, "$options": "i"}},
            ]
        return await r.get_by_filter(filter_, page=page, page_size=page_size)

    @router.get("/{item_id}", response_model=out_schema)
    async def get_item(
        item_id: str = Path(...),
        user: CurrentUser = Depends(get_current_user),
        r: BaseRepository = Depends(get_repo),
    ):
        if require_admin_read and user.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
        try:
            doc = await r.get_by_id(item_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if user.get("role") == "customer" and customer_owns and doc.get(owner_field) != user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your record")
        return doc

    @router.put("/{item_id}", response_model=out_schema)
    async def update_item(
        item_id: str = Path(...),
        payload: update_schema = ...,  # type: ignore[valid-type]
        user: CurrentUser = Depends(get_current_user),
        r: BaseRepository = Depends(get_repo),
    ):
        if require_admin_update and user.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
        try:
            doc = await r.get_by_id(item_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if user.get("role") == "customer" and customer_owns and doc.get(owner_field) != user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your record")
        return await r.update_by_id(item_id, payload.model_dump(exclude_unset=True))

    if admin_delete:
        @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_item(
            item_id: str = Path(...),
            user: AdminUser = Depends(require_role("admin")),
            r: BaseRepository = Depends(get_repo),
        ):
            try:
                ok = await r.delete_by_id(item_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
            if not ok:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            return None

    return router
