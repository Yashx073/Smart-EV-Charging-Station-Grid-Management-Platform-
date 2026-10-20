from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import close_db, connect_db, init_indexes
from app.routers import (
    ac_ports,
    admin,
    auth,
    battery,
    bookings,
    corrective,
    dashboard,
    dc_fast_ports,
    evs,
    grids,
    maintenance,
    nonrenewable,
    notifications,
    payments,
    phones,
    ports,
    preventive,
    renewable,
    schedules,
    sessions,
    sources,
    stations,
    tariffs,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await connect_db()
    await init_indexes(db)
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Smart EV Charging Station Management System (FastAPI + MongoDB)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["set-cookie"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(evs.router)
app.include_router(phones.router)
app.include_router(stations.router)
app.include_router(ports.router)
app.include_router(ac_ports.router)
app.include_router(dc_fast_ports.router)
app.include_router(tariffs.router)
app.include_router(bookings.router)
app.include_router(sessions.router)
app.include_router(payments.router)
app.include_router(maintenance.router)
app.include_router(preventive.router)
app.include_router(corrective.router)
app.include_router(schedules.router)
app.include_router(notifications.router)
app.include_router(battery.router)
app.include_router(grids.router)
app.include_router(sources.router)
app.include_router(renewable.router)
app.include_router(nonrenewable.router)
app.include_router(dashboard.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
