#!/usr/bin/env python3
"""Create or update the initial administrator account."""
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import MongoClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, "backend", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:changeme@localhost:27017/smart_ev_charging?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "smart_ev_charging")
ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "AdminPass123!")
ADMIN_NAME = os.getenv("SEED_ADMIN_FULL_NAME", "System Administrator")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def main():
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    now = datetime.now(timezone.utc)
    pwd = pwd_context.hash(ADMIN_PASSWORD)
    res = db["users"].update_one(
        {"email": ADMIN_EMAIL},
        {
            "$set": {
                "password_hash": pwd,
                "full_name": ADMIN_NAME,
                "role": "admin",
                "status": "active",
                "updated_at": now,
            },
            "$setOnInsert": {"email": ADMIN_EMAIL, "created_at": now},
        },
        upsert=True,
    )
    user = db["users"].find_one({"email": ADMIN_EMAIL})
    user_id = str(user["_id"])
    db["admins"].update_one(
        {"email": ADMIN_EMAIL},
        {
            "$setOnInsert": {
                "user_id": user_id,
                "email": ADMIN_EMAIL,
                "full_name": ADMIN_NAME,
                "privileges": ["manage_users", "manage_stations", "manage_tariffs", "manage_payments"],
                "created_at": now,
            }
        },
        upsert=True,
    )
    print(f"Admin ready: {ADMIN_EMAIL} (user id {user_id})")
    client.close()


if __name__ == "__main__":
    main()
