# API documentation

Base URL: `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs` (FastAPI OpenAPI). Authentication is via HttpOnly cookie `access_token` set on login; all state-changing endpoints send cookies with requests.

## Auth
- `POST /api/auth/register` {email, password, full_name, phone?} → User (customer)
- `POST /api/auth/login` {email, password} → {access_token, token_type}; sets cookie
- `POST /api/auth/logout` → clears cookie
- `GET /api/auth/me` → current User
- `GET /api/auth/admin/users` (admin) → paginated users

## Users (customer)
- `GET /api/users` → my EVs? (generic list filtered to owner)
- `GET /api/users/{id}`, `PUT /api/users/{id}`, `DELETE` (admin)

## EVs
- `POST /api/evs`, `GET /api/evs`, `GET /api/evs/{id}`, `PUT /api/evs/{id}`, `DELETE /api/evs/{id}` (admin)
- Customers can only manage their own EVs (owner_id set automatically).

## Stations / Ports / Tariffs
- `POST|GET|GET/{id}|PUT|DELETE` on `/api/stations`, `/api/ports`, `/api/tariffs` (admin create/update/delete; customers read-only).

## Bookings
- `POST /api/bookings` {ev_id, station_id, port_id, start_time, end_time} → Booking (customer)
- `GET /api/bookings` → my bookings (customer) or all (admin)
- `GET /api/bookings/{id}`
- `POST /api/bookings/{id}/cancel` → cancelled Booking
- `PUT /api/bookings/{id}/status` {status} (admin)

## Sessions
- `POST /api/sessions/start` {booking_id?, port_id} → Session
- `POST /api/sessions/{id}/end` {energy_delivered_kwh} → Session + payment
- `GET /api/sessions`, `GET /api/sessions/{id}`

## Payments
- `GET /api/payments` (my or all), `GET /api/payments/{id}`

## Maintenance / Schedules / Notifications / Grids / Sources / etc.
Full CRUD under `/api/maintenance`, `/api/schedules`, `/api/notifications`, `/api/grids`, `/api/sources`, `/api/renewable-sources`, `/api/non-renewable-sources`, `/api/battery-status`, `/api/preventive-maintenance`, `/api/corrective-maintenance`, `/api/user-phones`.

## Admin
- `/api/admin/users` list; `PUT|DELETE /api/admin/users/{id}`; admin-only.

## Dashboard
- `GET /api/dashboard/stats` → totals
- `GET /api/dashboard/trends?days=7` → booking_trend, revenue_trend, energy_trend

## Status codes
200 OK, 201 Created, 204 No Content, 400 Bad Request (validation/overlap), 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict (duplicate email).
