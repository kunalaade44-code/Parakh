# 🏛️ Dogfood 2026 Platform Architecture

## 1. System Topology

```
                   OFFLINE LAPTOP / HOST
                             │
                     docker compose up
                             │
             ┌───────────────┴───────────────┐
             ▼                               ▼
       Nginx / React UI               FastAPI Backend
       (Port 80 / 8080)               (Port 8000)
             │                               │
             └───────────────┬───────────────┘
                             ▼
                    SQLAlchemy ORM
                             ▼
                Local Database (Postgres/SQLite)
                             ▼
                 Auto-Seeded fixtures.json
```

## 2. Security & Backend Judge Isolation

The platform implements zero-trust isolation at the API gateway layer:

1. **Role Enforcement**: Authorization is enforced directly in FastAPI route dependencies (`require_organizer`, `require_judge`, `require_participant`).
2. **Strict Peer Block**: When a judge attempts to read scores using another judge's identifier (e.g. `GET /api/judge/scores?judge=jdg_01` as `judge_b`), the backend immediately aborts and returns **`HTTP 403 Forbidden`**.
3. **Participant Access Block**: Participants querying `/api/judge/scores` are denied with `HTTP 403`.
4. **Deadline Enforcement**: Project submissions check server-side UTC timestamps against `events.submissions_close` and return `HTTP 400 Bad Request` once the deadline has elapsed.
