# Architecture

## Diagram
```mermaid
flowchart TD
    subgraph Frontend [React + Vite + Tailwind]
      UI[Browser UI]
      AX[Axios API client]
    end
    subgraph Backend [FastAPI + Python]
      API[REST routes /api/*]
      AUTH[JWT auth + HttpOnly cookies]
      SVC[Booking & Session services]
    end
    subgraph DB[(MongoDB smart_ev_charging)]
      collections[20 collections + indexes + validators]
    end
    subgraph Docker [MongoDB container]
      mongo[mongod:7 + persistent volume]
    end

    UI --> AX
    AX --> API
    API --> AUTH
    AUTH --> SVC
    SVC --> collections
    collections --> mongo
```

## Layers
- **Frontend**: single-page React app served by Vite dev server (port 5173). Calls backend through Vite proxy (`/api` → `http://localhost:8000`). Uses HttpOnly cookies (set by backend) for session auth; no token stored in JS.
- **Backend**: FastAPI (port 8000). Stateless route handlers delegate to service layer. Auth via JWT in HttpOnly, SameSite cookie. Role-based dependencies guard customer vs admin routes.
- **Database**: MongoDB Community 7.x in Docker with a named persistent volume (`smart_ev_mongodb_data`). Connection URI read from `MONGODB_URI`. PyMongo/Motor async driver.
- **Concurrency**: booking slot locks use a unique index on `(port_id, slot_start)` to serialize concurrent reservations without requiring MongoDB transactions (standalone deployment).

## Security
- Passwords hashed with Argon2 (never stored plaintext).
- JWT access token in HttpOnly, SameSite=Lax cookie (Secure in production).
- Role-based authorization on every mutating route; customers cannot access other customers' resources by ID.
- CORS restricted to frontend origin with credentials.
- Secrets only in `.env` (never committed).
