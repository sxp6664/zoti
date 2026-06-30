# Zoti — AI Self Check-In System
> Live demo: _coming soon_ · Repo: https://github.com/sxp6664/zoti
A self-service hotel check-in kiosk. A guest finds their reservation (by last
name, or by **scanning their ID** with OCR auto-fill), selects a room, pays
(Stripe test mode), and receives a **digital room key** — no front-desk staff
required. Staff get role-based dashboards for rooms, housekeeping, and
manager analytics.

## Guest flow

```
Arrive ─▶ Look up reservation ─┬─ by last name
                               └─ by ID scan (OCR → auto-fill)
        ─▶ Select room ─▶ Pay (Stripe test) ─▶ Digital key issued ✓
```

## Architecture

```
React kiosk (Vite)
       │  REST
       ▼
FastAPI ──┬── JWT auth + RBAC (guest/receptionist/housekeeping/manager)
          ├── PostgreSQL (users, rooms, reservations)   [SQLAlchemy]
          ├── Redis (room-list cache, cache-aside + invalidation)
          ├── AWS Textract (ID OCR; mock provider when no AWS key)
          └── Stripe (test-mode payments; mock when no key)
       │
       ▼
Dockerized · GitHub Actions CI · deploy to AWS
```

## Run it

```bash
docker compose up --build
```

- Kiosk UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Seeded reservations to try at the kiosk: last name **Patel** (`ZOTI-1001`),
**Nguyen** (`ZOTI-1002`), **Garcia** (`ZOTI-1003`).
Staff logins (password `password`): `manager@zoti.dev`, `front@zoti.dev`,
`clean@zoti.dev`.

Runs fully offline by default: OCR uses a **mock** provider and payments
**mock-complete** until you add real keys. To enable real services, set
`OCR_PROVIDER=textract` (+ AWS creds) and `STRIPE_SECRET_KEY=sk_test_...`.

## Design decisions (the "why")

- **RBAC at one enforcement point.** The JWT carries a role claim; a single
  `require_roles(...)` dependency gates every staff route. Adding a role or
  protecting a route is a one-liner, and there's no scattered auth logic.
- **Cache-aside with Redis + explicit invalidation.** Room lists are read
  far more than written, so they're cached with a short TTL and the cache is
  busted on any write (e.g. housekeeping marking a room clean). This is the
  classic read-heavy optimization, done with correct invalidation.
- **OCR behind a provider seam.** `services/ocr.py` exposes one function;
  Textract vs. mock is an env switch. The app never depends on AWS being
  present, which keeps local dev and CI fast and free.
- **Payments isolated + test-mode only.** No real card data ever touches the
  system; Stripe runs in test mode and the flow degrades to a mock when no
  key is set. Honest scope for a portfolio project.
- **Digital key, not hardware.** Check-in issues a generated key code rather
  than integrating a physical lock — the realistic software boundary.

## Roadmap

- [x] Auth + RBAC, rooms, reservations, seed data
- [x] Self-check-in flow: lookup, room select, pay, key issue
- [x] ID-scan OCR (Textract + mock providers)
- [x] Redis caching, manager analytics, React kiosk UI
- [x] Dockerized, GitHub Actions CI
- [ ] Deploy to AWS (ECS Fargate + RDS + ElastiCache)
- [ ] **Future add-on:** optional selfie ↔ ID-photo face match (with a clear
      privacy/consent design) — deliberately out of the MVP.

## Security note

This is a portfolio project. Real biometric check-in carries significant
privacy and legal obligations (BIPA, GDPR); the optional face-match feature
is intentionally deferred and would require consent flows and a data-handling
design before it belonged anywhere near production.
