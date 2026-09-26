# 🏆 Dogfood 2026 Hackathon Platform

An enterprise-grade, offline-first hackathon submission and judging system built with **FastAPI**, **React**, and **PostgreSQL/SQLite**. Fully compliant with the DOGFOOD 2026 specification, featuring **strict backend judge isolation**, **multi-judge score normalization**, and **real-time operations**.

---

## ⚡ Quick Start (Offline / Self-Contained)

The platform runs completely self-contained with no cloud dependencies or external network access.

```bash
# 1. Boot local stack with Docker
docker compose up
```

The database automatically seeds with 40+ projects, 30 judges, and 8 tracks from `fixtures.json`.

---

## 🔑 Test Authentication Logins

When the system boots, test session cookies are automatically provisioned:

| Role | Session Cookie Header | Notes |
|---|---|---|
| **Organizer** | `Cookie: session=org_7f2a` | Full admin & CSV export access |
| **Judge A** | `Cookie: session=jdg_a_91bc` | Reviewer profile with isolated views |
| **Judge B** | `Cookie: session=jdg_b_44de` | Peer judge (cannot inspect Judge A) |
| **Participant** | `Cookie: session=prt_2e88` | Blocked from judging data |

---

## 🧪 Acceptance Test Suite

Run the automated acceptance suite verifying all T1 and T2 assertions:

```bash
python run.py .dogfood.toml
```

Output:
```
DOGFOOD 2026 acceptance report
portal: http://127.0.0.1:8000
claimed: T1 T2
fixtures: fixtures.json

T1  gallery is public ................. PASS
T1  project from fixtures shown ....... PASS
T1  closed event refuses submissions .. PASS
T2  judge sees own scores ............. PASS
T2  judge cannot see peer scores ...... PASS
T2  participant blocked ............... PASS
T2  csv export works .................. PASS

claimed T1 T2, verified T1 T2
```

---

## 🏛️ Project Structure

```
.
├── .dogfood.toml          # Checker route & auth configuration
├── acceptance-report.txt  # Verified acceptance receipt
├── docker-compose.yml     # Offline Docker compose specification
├── fixtures.json          # Benchmark dataset
├── run.py                 # Acceptance checker suite
├── backend/               # FastAPI backend with SQLAlchemy ORM
├── frontend/              # Modern React + Tailwind CSS web interface
├── ARCHITECTURE.md        # System architecture & security design
├── DATA-MODEL.md          # Entity relational database schema
├── JUDGING.md             # Normalization algorithms & mathematical proofs
└── LICENSE                # MIT License
```
