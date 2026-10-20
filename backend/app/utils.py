from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def to_str_id(doc: dict | None) -> dict | None:
    if doc is None:
        return None
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    return out


def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise ValueError(f"Invalid ObjectId: {value}") from exc


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    raise ValueError(f"Expected datetime, got {type(value)}")


def paginate(page: int, page_size: int) -> tuple[int, int]:
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    skip = (page - 1) * page_size
    return skip, page_size
