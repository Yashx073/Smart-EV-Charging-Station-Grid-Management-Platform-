# Testing

## Backend tests
Framework: pytest + pytest-asyncio + httpx (ASGI client). Tests run against a **separate test database** (`smart_ev_charging_test`); the development database is never touched. Each test runs with a fresh Motor client and all collections are cleared between tests.

### Run
```
cd backend
.venv/bin/pytest -q
```

### Coverage
- Registration and login
- Password hashing (argon2): hash/verify, wrong password rejected
- Duplicate email rejection (409)
- Role-based authorization: customer cannot reach admin endpoints (403); admin can
- Invalid MongoDB ObjectIds → 400
- CRUD operations: EVs (create/list/update; customer delete → 403)
- Booking creation, overlap rejection (400), past start rejection (400)
- Concurrent booking attempts for same port/time → one 201, one 400 (slot-lock unique index)
- Booking cancellation; double-cancellation rejected (400)
- Customer data isolation: user only sees own bookings
- Charging session start/end; automatic billing
- Bill calculation: 20 kWh × ₹12/kWh = ₹240
- Duplicate billing prevention: re-ending a session → 400; duplicate start on occupied port → 400
- Maintenance CRUD (admin)
- Dashboard stats and trends
- Database connection failure handling (client reset between tests)

### Actual results (latest run)
```
16 passed, 2 warnings in ~3.2s
```
All 16 tests pass consistently across repeated runs. Tests were executed against MongoDB 7.x running in Docker.

### Frontend
```
cd frontend
npm run build   # TypeScript + Vite production build succeeds
```
The frontend build type-checks and bundles without errors. Frontend UI workflows are exercised manually through the running application (registration, login, booking, session, billing).
