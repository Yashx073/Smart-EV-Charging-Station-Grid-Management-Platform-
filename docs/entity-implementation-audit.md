# Entity Implementation Audit — All 22 Smart EV Entities

## Executive Summary
This audit compares the 22 required domain entities from the source-of-truth SQL relational schema (`smart_ev_charging.db` and ER specifications) against the existing MongoDB full-stack implementation in `smart-ev-charging`.

- **Total Entities Required:** 22
- **Fully Implemented Entities (before audit):** 0 (several were partially implemented but missed original SQL attributes, subtype references, or frontend integration)
- **Partially Implemented Entities:** 14 (`users`, `admins`, `tariffs`, `charging_stations`, `charging_ports`, `evs`, `grids`, `bookings`, `charging_sessions`, `payments`, `schedules`, `maintenance`, `notifications`, `battery_status`)
- **Missing or Incomplete Subtype Entities:** 8 (`source` parent collection, `ac_port`, `dc_fast_port`, `user_phone`, `renewable_source`, `non_renewable_source`, `preventive_maintenance`, `corrective_maintenance`)
- **Frontend Pages Status:** Missing dedicated UI management for Admins, Energy Sources (Parent, Renewable, Non-Renewable), Grids, Schedules, Notifications, Battery Status, ACPorts, DCFastPorts, UserPhones, and Maintenance Subtypes.

---

## Entity-by-Entity Audit Table

| # | Entity Name | Source SQL Table & Attributes | Current MongoDB Implementation | Implementation Status | Work Required |
|---|---|---|---|---|---|
| 1 | **EV_USER** | `ev_user`<br>• `user_id` (PK)<br>• `first_name`<br>• `last_name`<br>• `email` (UQ)<br>• `address`<br>• `date_of_birth` | `users` collection<br>• `_id` (ObjectId)<br>• `email` (UQ)<br>• `password_hash`<br>• `full_name`<br>• `phone`<br>• `role`<br>• `status`<br>• `created_at`, `updated_at` | **Partially Implemented** | Map `user_id`, `address`, `date_of_birth`, support first/last name decomposition and full_name. Ensure relationship resolution to `evs`, `user_phones`, `bookings`, `notifications`. |
| 2 | **ADMIN** | `admin`<br>• `admin_id` (PK)<br>• `admin_name`<br>• `email` (UQ)<br>• `phone_no`<br>• `role`<br>• `experience` (>=0) | `admins` collection<br>• `_id` (ObjectId)<br>• `user_id`<br>• `email` (UQ)<br>• `full_name`<br>• `privileges`<br>• `created_at` | **Partially Implemented** | Support `admin_id`, `phone_no`, `role`, `experience`. Link with `maintenance` (`admin_id`). Add admin management UI page and full CRUD. |
| 3 | **TARIFF** | `tariff`<br>• `tariff_id` (PK)<br>• `tariff_name`<br>• `rate_per_kwh` (>=0)<br>• `peak_hour_rate` (>=0)<br>• `off_peak_rate` (>=0) | `tariffs` collection<br>• `_id`<br>• `name` (UQ)<br>• `price_per_kwh`<br>• `valid_from`<br>• `valid_to`<br>• `is_active`<br>• `created_at` | **Partially Implemented** | Add `tariff_id`, `peak_hour_rate`, `off_peak_rate`, alias `rate_per_kwh` / `price_per_kwh`, connect to `charging_ports`. Complete UI form fields. |
| 4 | **SOURCE** | `source`<br>• `source_id` (PK)<br>• `source_name`<br>• `source_type` (RENEWABLE / NON_RENEWABLE)<br>• `capacity` (>=0)<br>• `status` (ACTIVE/INACTIVE/MAINTENANCE) | `sources` collection exists as route, but was not seeded; had no link to subtypes. | **Partially Implemented / Incomplete** | Implement `sources` collection with `source_id`, `source_name`, `source_type`, `capacity`, `unit`, `status`. Connect to `grid` and link to `renewable_sources` and `non_renewable_sources`. |
| 5 | **CHARGING_STATION** | `charging_station`<br>• `station_id` (PK)<br>• `station_name`<br>• `address`<br>• `latitude`<br>• `longitude`<br>• `operating_hours`<br>• `status` (ACTIVE/INACTIVE/MAINTENANCE) | `charging_stations` collection<br>• `_id`<br>• `name`<br>• `station_code` (UQ)<br>• `address`, `city`<br>• `latitude`, `longitude`<br>• `status`<br>• `created_at` | **Partially Implemented** | Support `station_id`, `operating_hours`, `grid_id`, `total_ports`. Connect relationships to `charging_ports`, `schedules`, `maintenance`, and `grids`. |
| 6 | **EV** | `ev`<br>• `ev_id` (PK)<br>• `vehicle_number` (UQ)<br>• `brand`<br>• `model`<br>• `battery_capacity` (>0)<br>• `manufacturing_year`<br>• `user_id` (FK) | `evs` collection<br>• `_id`<br>• `owner_id` (user_id)<br>• `model`<br>• `registration_number`<br>• `battery_capacity_kwh`<br>• `connector_type`<br>• `is_active`<br>• `created_at` | **Partially Implemented** | Support `ev_id`, `vehicle_number` / `registration_number`, `brand` / manufacturer, `manufacturing_year`, `status`. Connect to `battery_status` and `bookings`. |
| 7 | **USER_PHONE** | `user_phone`<br>• `user_id` (PK, FK)<br>• `phone_no` (PK) | `user_phones` collection<br>• `_id`<br>• `user_id`<br>• `number`<br>• `label`<br>• `created_at` (0 documents seeded, no UI) | **Missing / Incomplete** | Support `phone_no` / `number`, `phone_type` / `label`, `is_primary`, compound unique index on `(user_id, phone_no)`. Add CRUD endpoints and UI page/tab. |
| 8 | **GRID** | `grid`<br>• `grid_id` (PK)<br>• `grid_name`<br>• `voltage_level`<br>• `capacity` (>=0)<br>• `status`<br>• `source_id` (FK) | `grids` collection<br>• `_id`<br>• `name`<br>• `capacity_kw`<br>• `current_load_kw`<br>• `status`<br>• `created_at` | **Partially Implemented** | Add `grid_id`, `voltage_level`, `source_id` FK reference to `sources`. Connect to `charging_stations`. Add UI management page. |
| 9 | **CHARGING_PORT** | `charging_port`<br>• `station_id` (PK, FK)<br>• `port_number` (PK)<br>• `charger_type` (AC/DC_FAST)<br>• `power_output` (>0)<br>• `availability_status`<br>• `tariff_id` (FK) | `charging_ports` collection<br>• `_id`<br>• `station_id`<br>• `station_code`<br>• `port_number`<br>• `connector_type`<br>• `rated_power_kw`<br>• `status`<br>• `created_at` | **Partially Implemented** | Enforce compound unique `(station_id, port_number)`. Connect to `tariff_id`, `ac_port`, `dc_fast_port`, `bookings`, `charging_sessions`. Support `charger_type`. |
| 10 | **AC_PORT** | `ac_port`<br>• `station_id` (PK, FK)<br>• `port_number` (PK, FK)<br>• `connector_standard`<br>• `ac_phase` (SINGLE/THREE) | None (Missing collection, missing schemas, missing routes, missing UI) | **Missing** | Implement `ac_ports` collection, schema, compound key `(station_id, port_number)` / `port_id` FK, CRUD endpoints, validation, seed data, and frontend screen. |
| 11 | **DC_FAST_PORT** | `dc_fast_port`<br>• `station_id` (PK, FK)<br>• `port_number` (PK, FK)<br>• `dc_voltage` (>0)<br>• `maximum_current` (>0) | None (Missing collection, missing schemas, missing routes, missing UI) | **Missing** | Implement `dc_fast_ports` collection, schema, compound key `(station_id, port_number)` / `port_id` FK, CRUD endpoints, validation, seed data, and frontend screen. |
| 12 | **BOOKING** | `booking`<br>• `booking_id` (PK)<br>• `booking_date`<br>• `booking_time`<br>• `start_time`<br>• `end_time`<br>• `booking_status`<br>• `user_id` (FK)<br>• `ev_id` (FK)<br>• `station_id` (FK)<br>• `port_number` (FK) | `bookings` collection<br>• `_id`<br>• `user_id`<br>• `ev_id`<br>• `station_id`<br>• `port_id`<br>• `start_time`<br>• `end_time`<br>• `status`<br>• `created_at` | **Partially Implemented** | Support `booking_id`, `booking_date`, `booking_time`, `port_number` resolution. Maintain Business Logic A (overlap check & slot locks). Link to `charging_sessions`. |
| 13 | **CHARGING_SESSION** | `charging_session`<br>• `session_id` (PK)<br>• `start_time`<br>• `end_time`<br>• `energy_consumed` (>=0)<br>• `session_status`<br>• `booking_id` (UQ, FK) | `charging_sessions` collection<br>• `_id`<br>• `booking_id`<br>• `user_id`<br>• `ev_id`<br>• `port_id`<br>• `started_at`, `ended_at`<br>• `energy_delivered_kwh`<br>• `total_amount`<br>• `tariff_price_per_kwh`<br>• `status` | **Partially Implemented** | Support `session_id`, `energy_consumed`, `session_status`. Maintain Business Logic B (energy * tariff = total_amount & auto payment). Link to `payment`. |
| 14 | **PAYMENT** | `payment`<br>• `payment_id` (PK)<br>• `amount` (>=0)<br>• `payment_mode` (CASH/CARD/UPI/NET_BANKING/WALLET)<br>• `payment_date`<br>• `payment_status`<br>• `session_id` (UQ, FK) | `payments` collection<br>• `_id`<br>• `session_id` (UQ)<br>• `user_id`<br>• `amount`<br>• `payment_method`<br>• `transaction_reference` (UQ)<br>• `status`<br>• `created_at` | **Partially Implemented** | Support `payment_id`, `payment_mode`, `payment_date`, `payment_status`. Connect to `session_id`. Prevent duplicate transactions. |
| 15 | **SCHEDULE** | `schedule`<br>• `schedule_id` (PK)<br>• `schedule_date`<br>• `start_time`<br>• `end_time`<br>• `available_slots` (>=0)<br>• `station_id` (FK) | `schedules` collection (0 documents, generic crud_router, no UI page) | **Missing / Incomplete** | Support `schedule_id`, `schedule_date`, `start_time`, `end_time`, `available_slots`, `station_id`, `port_id`. Add UI page and relationship resolution. |
| 16 | **MAINTENANCE** | `maintenance`<br>• `maintenance_id` (PK)<br>• `maintenance_date` / `scheduled_date`<br>• `maintenance_type` (PREVENTIVE/CORRECTIVE)<br>• `description`<br>• `status`<br>• `cost` (>=0)<br>• `station_id` (FK)<br>• `admin_id` (FK) | `maintenance` collection<br>• `_id`<br>• `station_id`<br>• `port_id`<br>• `title`, `description`<br>• `scheduled_date`<br>• `status`<br>• `created_at` | **Partially Implemented** | Add `maintenance_id`, `maintenance_type`, `admin_id` FK reference, `cost`. Connect to `preventive_maintenance` and `corrective_maintenance`. Enhance UI page. |
| 17 | **NOTIFICATION** | `notification`<br>• `notification_id` (PK)<br>• `message`<br>• `notification_type`<br>• `sent_date`<br>• `read_status`<br>• `user_id` (FK) | `notifications` collection<br>• `_id`<br>• `user_id`<br>• `message`<br>• `is_read`<br>• `created_at` (No UI page) | **Partially Implemented** | Add `notification_id`, `notification_type`, `read_status` / `is_read`, `sent_date` / `created_at`. Add frontend notifications page/bell view. |
| 18 | **BATTERY_STATUS** | `battery_status`<br>• `battery_status_id` (PK)<br>• `current_level` (0-100)<br>• `charging_level` (0-100)<br>• `health_status`<br>• `last_updated`<br>• `ev_id` (UQ, FK) | `battery_status` collection<br>• `_id`<br>• `ev_id`<br>• `battery_percentage`<br>• `temperature_c`<br>• `recorded_at` (No UI page) | **Partially Implemented** | Add `battery_status_id`, `current_level`, `charging_level`, `health_status`, `last_updated`. Enforce `ev_id` FK uniqueness. Add frontend UI page/view. |
| 19 | **RENEWABLE_SOURCE** | `renewable_source`<br>• `source_id` (PK, FK)<br>• `renewable_type`<br>• `generation_efficiency` (0-100) | `renewable_sources` collection<br>• `_id`<br>• `name`<br>• `source_type`<br>• `capacity_kw`<br>• `energy_generated_kwh` (No parent FK to source, no UI) | **Incomplete / Disconnected** | Link `source_id` FK to `sources`, support `renewable_type`, `generation_efficiency`, parent-child subtype relationship, and UI management. |
| 20 | **NON_RENEWABLE_SOURCE** | `non_renewable_source`<br>• `source_id` (PK, FK)<br>• `fuel_type`<br>• `emission_rate` (>=0) | `non_renewable_sources` collection<br>• `_id`<br>• `name`<br>• `source_type`<br>• `capacity_kw`<br>• `energy_generated_kwh` (No parent FK to source, no UI) | **Incomplete / Disconnected** | Link `source_id` FK to `sources`, support `fuel_type`, `emission_rate`, parent-child subtype relationship, and UI management. |
| 21 | **PREVENTIVE_MAINTENANCE** | `preventive_maintenance`<br>• `maintenance_id` (PK, FK)<br>• `maintenance_interval` (>0)<br>• `next_due_date` | `preventive_maintenance` collection (0 documents, generic crud_router with station_id, missing maintenance_id FK) | **Incomplete / Disconnected** | Link `maintenance_id` FK to `maintenance`, support `maintenance_interval`, `next_due_date`, checklist/result, and UI integration. |
| 22 | **CORRECTIVE_MAINTENANCE** | `corrective_maintenance`<br>• `maintenance_id` (PK, FK)<br>• `fault_description`<br>• `repair_action` | `corrective_maintenance` collection (0 documents, generic crud_router with station_id, missing maintenance_id FK) | **Incomplete / Disconnected** | Link `maintenance_id` FK to `maintenance`, support `fault_description`, `repair_action`, severity/downtime, and UI integration. |

---

## Detailed Plan of Action

1. **Database Schema & Initialization (`database.py`):**
   - Add collection constants: `AC_PORTS = "ac_ports"`, `DC_FAST_PORTS = "dc_fast_ports"`.
   - Update indexes to support original keys and foreign keys:
     - `ac_ports`: `([("station_id", ASCENDING), ("port_number", ASCENDING)], unique=True)`, `port_id`.
     - `dc_fast_ports`: `([("station_id", ASCENDING), ("port_number", ASCENDING)], unique=True)`, `port_id`.
     - `sources`: `name`, `source_id` (unique, sparse).
     - `renewable_sources`: `source_id` (unique, sparse).
     - `non_renewable_sources`: `source_id` (unique, sparse).
     - `preventive_maintenance`: `maintenance_id` (unique, sparse).
     - `corrective_maintenance`: `maintenance_id` (unique, sparse).
     - `user_phones`: `([("user_id", ASCENDING), ("phone_no", ASCENDING)], unique=True)`.
     - `battery_status`: `ev_id` (unique).
     - `schedules`: `station_id`, `schedule_date`.
     - `charging_stations`: `grid_id`.
     - `grids`: `source_id`.
     - `maintenance`: `admin_id`, `station_id`.
     - `admins`: `admin_id` (unique, sparse).
     - `ev_user`: `user_id` (unique, sparse).
     - `ev`: `ev_id` (unique, sparse), `vehicle_number`.
     - `charging_port`: `port_id` (unique, sparse), `tariff_id`.
     - `booking`: `booking_id` (unique, sparse).
     - `charging_session`: `session_id` (unique, sparse).
     - `payment`: `payment_id` (unique, sparse).
     - `schedule`: `schedule_id` (unique, sparse).
     - `maintenance`: `maintenance_id` (unique, sparse).
     - `notification`: `notification_id` (unique, sparse).
     - `battery_status`: `battery_status_id` (unique, sparse).
   - Add MongoDB validation schemas for constraints (ranges, enums).

2. **Pydantic Schemas (`schemas.py`):**
   - Update and harmonize models for all 22 entities, ensuring all SQL source attributes and MongoDB fields are supported (with aliases/fallbacks so both field name conventions serialize and deserialize smoothly).
   - Add models for `ACPortCreate`, `ACPortUpdate`, `ACPortOut`.
   - Add models for `DCFastPortCreate`, `DCFastPortUpdate`, `DCFastPortOut`.
   - Add comprehensive models for `AdminCreate`, `AdminUpdate`, `AdminOut`.
   - Add parent-subtype schemas for `Source`, `RenewableSource`, `NonRenewableSource`.
   - Add parent-subtype schemas for `Maintenance`, `PreventiveMaintenance`, `CorrectiveMaintenance`.
   - Add `UserPhoneCreate`, `UserPhoneUpdate`, `UserPhoneOut`.
   - Add `ScheduleCreate`, `ScheduleUpdate`, `ScheduleOut`.
   - Add `NotificationCreate`, `NotificationUpdate`, `NotificationOut`.
   - Add `BatteryStatusCreate`, `BatteryStatusUpdate`, `BatteryStatusOut`.

3. **Backend Repositories & Services:**
   - Implement reference resolution services:
     - Port -> AC_PORT or DC_FAST_PORT subtype lookup.
     - Source -> Renewable / Non-Renewable subtype lookup.
     - Maintenance -> Preventive / Corrective subtype lookup.
     - User -> User Phones lookup.
     - Station -> Grid, Ports, Maintenance, Schedules lookup.
     - EV -> Battery Status lookup.
     - Admin -> Maintenance lookup.
   - Maintain Business Logic A (booking validation, slot locking).
   - Maintain Business Logic B (session start/end, auto bill calculation `kwh * rate`).

4. **Backend Routers (`routers/`):**
   - Implement `/api/ac-ports` router.
   - Implement `/api/dc-fast-ports` router.
   - Extend `/api/sources` router to manage parent source records with subtype associations.
   - Extend `/api/renewable-sources` and `/api/non-renewable-sources` to validate parent `source_id`.
   - Extend `/api/preventive-maintenance` and `/api/corrective-maintenance` to validate parent `maintenance_id`.
   - Enhance `/api/admins` router with full admin profile CRUD and permission checks.
   - Enhance `/api/user-phones` router.
   - Register all routers in `main.py`.

5. **Database Seeding & Verification Script:**
   - Update `scripts/seed_database.py` to seed all 22 entities with real, relational-coherent documents derived from the SQL baseline.
   - Create `scripts/verify_database.py` to check presence, indexes, validators, and record counts across all 22 entities.

6. **Frontend Enhancements (`frontend/`):**
   - Update `frontend/src/types/index.ts` with TypeScript types for all 22 entities.
   - Create pages and navigation for:
     - Sources (Parent + Renewable + Non-Renewable tabs/views)
     - Grids (with connected sources and stations)
     - AC & DC Fast Ports (subtypes under Ports)
     - Schedules
     - Notifications
     - Battery Status
     - Admins
     - User Phones (under Profile / Users)
     - Preventive & Corrective Maintenance (under Maintenance)
   - Update `App.tsx` routes and `MainLayout.tsx` navigation.
   - Verify frontend production build.

7. **Automated Testing (`backend/tests/`):**
   - Write comprehensive tests for all 22 entities, relationships, constraints, CRUD operations, RBAC, Business Logic A & B, and subtype integrity.
   - Run tests and report actual pass/fail results.

8. **Documentation:**
   - Update `docs/database-design.md` with complete collection-by-collection schemas.
   - Create `docs/entity-implementation-report.md`.
