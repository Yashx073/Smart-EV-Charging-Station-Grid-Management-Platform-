from typing import Any, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import CHARGING_PORTS, CHARGING_STATIONS, TARIFFS, get_db
from app.dependencies import AdminUser, CurrentUser, get_current_user, require_role
from app.schemas import PortCreate, PortOut, PortUpdate
from app.utils import to_object_id, to_str_id, utc_now

router = APIRouter(prefix="/api/ports", tags=["ports"])


def _oid(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id") from exc


@router.post("", response_model=PortOut, status_code=status.HTTP_201_CREATED)
async def create_port(
    payload: PortCreate,
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    data = payload.model_dump()
    station_id = data["station_id"]

    # Verify station exists
    stn = await db[CHARGING_STATIONS].find_one({"_id": _oid(station_id)})
    if not stn:
        stn = await db[CHARGING_STATIONS].find_one({"station_id": station_id})
    if not stn:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Charging station not found")

    data["station_code"] = stn.get("station_code")

    # Check unique (station_id, port_number)
    existing = await db[CHARGING_PORTS].find_one(
        {"station_id": station_id, "port_number": data["port_number"]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Port number {data['port_number']} already exists at this station",
        )

    # If tariff_id provided, verify
    if data.get("tariff_id"):
        tariff = await db[TARIFFS].find_one({"_id": _oid(data["tariff_id"])})
        if not tariff:
            tariff = await db[TARIFFS].find_one({"tariff_id": data["tariff_id"]})
        if not tariff:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced tariff not found")

    now = utc_now()
    data["created_at"] = now
    data["updated_at"] = now

    res = await db[CHARGING_PORTS].insert_one(data)
    data["_id"] = res.inserted_id

    # Update station total_ports count
    count = await db[CHARGING_PORTS].count_documents({"station_id": station_id})
    await db[CHARGING_STATIONS].update_one({"_id": stn["_id"]}, {"$set": {"total_ports": count}})

    return to_str_id(data)


@router.get("", response_model=dict)
async def list_ports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    station_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    charger_type: Optional[str] = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filter_: dict[str, Any] = {}
    if station_id:
        filter_["station_id"] = station_id
    if status_filter:
        filter_["$or"] = [{"status": status_filter}, {"availability_status": status_filter}]
    if charger_type:
        filter_["$or"] = [{"charger_type": charger_type}, {"connector_type": charger_type}]

    skip = (page - 1) * page_size
    cursor = db[CHARGING_PORTS].find(filter_).skip(skip).limit(page_size)
    total = await db[CHARGING_PORTS].count_documents(filter_)
    items = [to_str_id(d) async for d in cursor]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{item_id}", response_model=PortOut)
async def get_port(
    item_id: str = Path(...),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CHARGING_PORTS].find_one({"_id": _oid(item_id)})
    if not doc:
        doc = await db[CHARGING_PORTS].find_one({"port_id": item_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charging port not found")
    return to_str_id(doc)


@router.put("/{item_id}", response_model=PortOut)
async def update_port(
    item_id: str = Path(...),
    payload: PortUpdate = ...,  # type: ignore[valid-type]
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CHARGING_PORTS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charging port not found")

    data = payload.model_dump(exclude_unset=True)
    if "tariff_id" in data and data["tariff_id"]:
        tariff = await db[TARIFFS].find_one({"_id": _oid(data["tariff_id"])})
        if not tariff:
            tariff = await db[TARIFFS].find_one({"tariff_id": data["tariff_id"]})
        if not tariff:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referenced tariff not found")

    data["updated_at"] = utc_now()
    await db[CHARGING_PORTS].update_one({"_id": _oid(item_id)}, {"$set": data})
    updated = await db[CHARGING_PORTS].find_one({"_id": _oid(item_id)})
    return to_str_id(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_port(
    item_id: str = Path(...),
    user: AdminUser = Depends(require_role("admin")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db[CHARGING_PORTS].find_one({"_id": _oid(item_id)})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charging port not found")

    res = await db[CHARGING_PORTS].delete_one({"_id": _oid(item_id)})
    if res.deleted_count > 0:
        count = await db[CHARGING_PORTS].count_documents({"station_id": doc["station_id"]})
        try:
            await db[CHARGING_STATIONS].update_one(
                {"_id": _oid(doc["station_id"])}, {"$set": {"total_ports": count}}
            )
        except Exception:
            pass
    return None
