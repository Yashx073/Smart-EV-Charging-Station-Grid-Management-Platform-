# Smart EV Charging Station Management System

## Overview
A complete, locally runnable full-stack web application for managing electric-vehicle charging stations. It uses **MongoDB** as its primary database and implements real backend business logic (booking with concurrency control, and charging sessions with automatic billing) rather than a UI prototype.

## Features
- User registration, login, logout with JWT in HttpOnly cookies
- Role-based access control (customer / admin)
- Customer: manage profile & EVs, view stations/ports, book & cancel charging ports, view sessions/bills/payments/notifications
- Admin: manage users, stations, ports, tariffs, grids, energy sources, maintenance, schedules; view all bookings/sessions/payments
- Business Logic 1: EV charging booking with port availability and overlap rejection (optimistic slot-lock concurrency control)
- Business Logic 2: Charging session start/end with automatic bill calculation (energy × tariff price)
- Dashboard with summary cards and Recharts trends
- Simulated payments (no real payment processor)
- Soft delete / archival for financial records
- Pagination, filtering, loading/empty/error states, confirmation dialogs
- Automated backend tests (pytest) with documented results

## Technology Stack
Frontend: React, Vite, TypeScript, Tailwind CSS, React Router, Axios, Recharts, Lucide React, React Hook Form + Zod
Backend: Python 3.11, FastAPI, PyMongo/Motor, Pydantic, JWT (python-jose), Argon2 (passlib), python-dotenv
Database: MongoDB Community Server (Docker), database `smart_ev_charging`

## Project Structure
```
smart-ev-charging/
├── frontend/            # React + Vite + TypeScript + Tailwind
├── backend/             # FastAPI app
│   ├── app/             # config, database, security, routers, services, schemas, utils
│   ├── tests/           # pytest backend tests
│   ├── requirements.txt
│   └── .env.example
├── scripts/             # seed_database.py, create_admin.py
├── docs/                # architecture, database-design, api-documentation, testing
├── docker-compose.yml   # MongoDB with persistent named volume
├── run.sh               # one-command startup
├── .gitignore
└── README.md
```

## Prerequisites
- Docker + Docker Compose (for MongoDB)
- Python 3.11+
- Node.js 20 + npm
- A working Docker daemon

## MongoDB setup
Start MongoDB with:
```
docker compose up -d mongodb
```
Data persists in the named volume `smart_ev_mongodb_data`. The container binds to `127.0.0.1:27017` only (not exposed publicly).

## Backend setup
```
cd backend
cp .env.example .env   # edit secrets
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
Edit `.env` with your own `SECRET_KEY`, MongoDB credentials, and seed admin password.

## Frontend setup
```
cd frontend
npm install
```

## Database seeding
```
cd backend
.venv/bin/python ../scripts/seed_database.py
```
The seed script is idempotent. It creates customers, an admin, stations, ports, EVs, tariffs, and sample bookings/sessions/payments.

Demo credentials (development only, set via `.env`):
- Admin: `admin@evcharging.local` / `AdminPass123!`
- Customer: `alice@example.com` / `CustomerPass123!`

## Startup (one command)
From the project root:
```
chmod +x run.sh
./run.sh
```
This starts MongoDB, creates the Python venv, installs dependencies, seeds the DB, and launches the backend (http://localhost:8000) and frontend (http://localhost:5173).

API documentation: http://localhost:8000/docs

## Shutdown
Press Ctrl+C in the `./run.sh` terminal. MongoDB data is preserved (the named volume is NOT removed).
To also remove MongoDB: `docker compose down -v`

## Running tests
Backend:
```
cd backend
.venv/bin/pytest -q
```
Frontend build:
```
cd frontend
npm run build
```

## The two mandatory business logics
1. **Booking & port availability** (`/api/bookings`): customer selects EV, station, port, start/end. Backend validates ownership, operational status, future interval, and overlapping active bookings. Overlap uses `existing_start < requested_end AND existing_end > requested_start`. Concurrency is controlled with a 30-minute slot-lock collection backed by a unique index `(port_id, slot_start)`, so simultaneous requests for the same port/time slot are serialized at the database level. Cancellations release the slot locks.
2. **Charging session & automatic billing** (`/api/sessions`): start a session for an eligible booking/port; end it with simulated energy delivered (kWh). The applicable tariff is retrieved and `total_amount = energy_kwh × price_per_kwh`. A session and its payment are saved atomically; duplicate starts and duplicate billing are prevented (unique indexes on `port_id` active session and `session_id` payment). Example: 20 kWh at ₹12/kWh = ₹240.

## Docs
- docs/architecture.md
- docs/database-design.md
- docs/api-documentation.md
- docs/testing.md
