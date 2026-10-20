from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import DC_FAST_PORTS, CHARGING_PORTS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.repository import BaseRepository
from app.schemas import DCFastPortCreate, DCFastPortOut, DCFastPortUpdate
from app.utils import to_str_id, to_object_id

router = APIRouter(prefix="/api/dc-fast-ports", tags=["dc-fast-ports"])


async def get_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> BaseRepository:
    return BaseRepository(db, DC_FAST_PORTS)


@router.post("", response_model=DCFastPortOut, status_code=status.HTTP_201_CREATED)
async def create_dc_fast_port(
    payload: DCFastPortCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
    r: BaseRepository = Depends(get_repo),
):
    data = payload.model_dump()
    # Validate parent CHARGING_PORT exists
    port_query = {"station_id": data["station_id"], "port_number": data["port_number"]}
    parent_port = await db[CHARGING_PORTS].find_one(port_query)
    if not parent_port and data.get("port_id"):
        try:
            parent_port = await db[CHARGING_PORTS].find_one({"_id": to_object_id(data["port_id"])})
        except Exception:
            pass

    if not parent_port:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent charging port for station {data['station_id']}, port {data['port_number']} not found",
        )

    data["port_id"] = str(parent_port["_id"])

    # Check for duplicate
    existing = await db[DC_FAST_PORTS].find_one(
        {"$or": [
            {"station_id": data["station_id"], "port_number": data["port_number"]},
            {"port_id": data["port_id"]},
        ]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DC Fast port specification already exists for this port",
        )

    return await r.create(data)


@router.get("", response_model=dict)
async def list_dc_fast_ports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: Optional[str] = Query(None),
    port_id: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    r: BaseRepository = Depends(get_repo),
):
    filter_: dict[str, Any] = {}
    if station_id:
        filter_["station_id"] = station_id
    if port_id:
        filter_["port_id"] = port_id
    return await r.get_by_filter(filter_, page=page, page_size=page_size)


@router.get("/{item_id}", response_model=DCFastPortOut)
async def get_dc_fast_port(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    r: BaseRepository = Depends(get_repo),
):
    try:
        doc = await r.get_by_id(item_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DC Fast Port not found")
    return doc


@router.put("/{item_id}", response_model=DCFastPortOut)
async def update_dc_fast_port(
    item_id: str = Path(...),
    payload: DCFastPortUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    r: BaseRepository = Depends(get_repo),
):
    try:
        doc = await r.get_by_id(item_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DC Fast Port not found")
    return await r.update_by_id(item_id, payload.model_dump(exclude_unset=True))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dc_fast_port(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    r: BaseRepository = Depends(get_repo),
):
    try:
        ok = await r.delete_by_id(item_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id")
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DC Fast Port not found")
    return None
