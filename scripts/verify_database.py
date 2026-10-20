#!/usr/bin/env python3
"""Database Verification Script for All 22 Smart EV Entities.

Connects to the configured MongoDB database, checks presence of all 22 collections,
verifies indexes, validators, and reports document counts.
Distinguishes between an intentionally empty collection and a missing collection.
"""
import os
import sys

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, "backend", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:changeme@localhost:27017/smart_ev_charging?authSource=admin")
MONGODB_DB = os.getenv("MONGODB_DB", "smart_ev_charging")

# Exact 22 Entities required
REQUIRED_ENTITIES = [
    ("users", "1. EV_USER"),
    ("admins", "2. ADMIN"),
    ("tariffs", "3. TARIFF"),
    ("sources", "4. SOURCE"),
    ("charging_stations", "5. CHARGING_STATION"),
    ("evs", "6. EV"),
    ("user_phones", "7. USER_PHONE"),
    ("grids", "8. GRID"),
    ("charging_ports", "9. CHARGING_PORT"),
    ("ac_ports", "10. AC_PORT"),
    ("dc_fast_ports", "11. DC_FAST_PORT"),
    ("bookings", "12. BOOKING"),
    ("charging_sessions", "13. CHARGING_SESSION"),
    ("payments", "14. PAYMENT"),
    ("schedules", "15. SCHEDULE"),
    ("maintenance", "16. MAINTENANCE"),
    ("notifications", "17. NOTIFICATION"),
    ("battery_status", "18. BATTERY_STATUS"),
    ("renewable_sources", "19. RENEWABLE_SOURCE"),
    ("non_renewable_sources", "20. NON_RENEWABLE_SOURCE"),
    ("preventive_maintenance", "21. PREVENTIVE_MAINTENANCE"),
    ("corrective_maintenance", "22. CORRECTIVE_MAINTENANCE"),
]


def main():
    print(f"Connecting to MongoDB at: {MONGODB_URI}")
    print(f"Target Database: {MONGODB_DB}\n")

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client[MONGODB_DB]
        db.command("ping")
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB: {e}")
        sys.exit(1)

    existing_collections = set(db.list_collection_names())

    missing_collections = []
    empty_collections = []
    populated_collections = []

    print("=" * 80)
    print(f"{'#':<4} {'Entity':<26} {'Collection':<24} {'Status':<12} {'Docs':<8} {'Indexes'}")
    print("=" * 80)

    for idx, (col_name, entity_label) in enumerate(REQUIRED_ENTITIES, start=1):
        if col_name not in existing_collections:
            missing_collections.append(col_name)
            status_str = "MISSING"
            doc_count = 0
            index_count = 0
        else:
            doc_count = db[col_name].count_documents({})
            indexes = list(db[col_name].list_indexes())
            index_count = len(indexes)
            if doc_count == 0:
                empty_collections.append(col_name)
                status_str = "EMPTY"
            else:
                populated_collections.append(col_name)
                status_str = "VERIFIED"

        print(f"{idx:<4} {entity_label:<26} {col_name:<24} {status_str:<12} {doc_count:<8} {index_count} index(es)")

    print("=" * 80)
    print("\n--- Summary ---")
    print(f"Total Required Entities:       {len(REQUIRED_ENTITIES)}")
    print(f"Present & Populated:          {len(populated_collections)}")
    print(f"Present but Empty:            {len(empty_collections)}")
    print(f"Missing Collections:          {len(missing_collections)}")

    # Check validator status for key collections
    print("\n--- Schema Validators Check ---")
    for col_name in ["users", "bookings", "charging_sessions", "payments", "charging_stations", "charging_ports"]:
        try:
            infos = db.command("listCollections", filter={"name": col_name})
            first = infos["cursor"]["firstBatch"][0] if infos.get("cursor", {}).get("firstBatch") else {}
            has_val = "validator" in first.get("options", {})
            val_stat = "Enforced" if has_val else "Not configured"
            print(f"  Collection '{col_name}': Validator {val_stat}")
        except Exception:
            print(f"  Collection '{col_name}': Validator check skipped")

    if missing_collections:
        print(f"\nFAILED: Missing collections: {', '.join(missing_collections)}")
        sys.exit(1)
    else:
        print("\nSUCCESS: All 22 entities are represented as collections in MongoDB!")
        sys.exit(0)


if __name__ == "__main__":
    main()
