from typing import Any, TypeVar

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.database import get_db
from app.utils import paginate, to_object_id, to_str_id, utc_now

T = TypeVar("T")


class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase, collection: str):
        self.db = db
        self.collection = db[collection]

    async def create(self, data: dict) -> dict:
        data = dict(data)
        data.setdefault("created_at", utc_now())
        data["updated_at"] = utc_now()
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return to_str_id(data)

    async def get_by_id(self, item_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": to_object_id(item_id)})
        return to_str_id(doc)

    async def get_by_filter(
        self,
        filter_: dict | None = None,
        page: int = 1,
        page_size: int = 20,
        sort: str | None = None,
        sort_desc: bool = False,
    ) -> dict[str, Any]:
        filter_ = filter_ or {}
        skip, limit = paginate(page, page_size)
        cursor = self.collection.find(filter_)
        if sort:
            cursor = cursor.sort(sort, DESCENDING if sort_desc else ASCENDING)
        total = await self.collection.count_documents(filter_)
        docs = [to_str_id(d) async for d in cursor.skip(skip).limit(limit)]
        return {"items": docs, "total": total, "page": page, "page_size": limit}

    async def update_by_id(self, item_id: str, data: dict) -> dict | None:
        data = {k: v for k, v in data.items() if v is not None}
        if not data:
            return await self.get_by_id(item_id)
        data["updated_at"] = utc_now()
        await self.collection.update_one({"_id": to_object_id(item_id)}, {"$set": data})
        return await self.get_by_id(item_id)

    async def delete_by_id(self, item_id: str) -> bool:
        res = await self.collection.delete_one({"_id": to_object_id(item_id)})
        return res.deleted_count > 0

    async def archive_by_id(self, item_id: str) -> dict | None:
        return await self.update_by_id(item_id, {"status": "archived", "deleted_at": utc_now()})
