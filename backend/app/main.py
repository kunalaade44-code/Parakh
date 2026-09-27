from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import router as api_router

import app.models.models

# Create database tables safely and auto-seed if empty
try:
    Base.metadata.create_all(bind=engine)
    from app.core.database import SessionLocal
    from app.models.models import Event, User, Track, Criterion, Judge, Session as UserSession
    from datetime import datetime
    
    db_check = SessionLocal()
    try:
        if not db_check.query(Event).first():
            # Seed default event
            event = Event(
                id="evt_01",
                name="Sample Hack 2026",
                description="Official Dogfood 2026 Hackathon benchmark event.",
                submissions_close=datetime(2026, 12, 31, 23, 59, 59)
            )
            db_check.add(event)
            db_check.commit()
            
            # Default Tracks
            for t_id, t_name in [("trk_ai", "AI / ML"), ("trk_web", "Web3 / Infrastructure"), ("trk_open", "Open Innovation")]:
                db_check.add(Track(id=t_id, event_id="evt_01", name=t_name))
            
            # Default Criteria
            for c_id, c_name, c_weight in [("crt_01", "functionality", 0.35), ("crt_02", "quality", 0.35), ("crt_03", "innovation", 0.30)]:
                db_check.add(Criterion(id=c_id, event_id="evt_01", name=c_name, weight=c_weight, description="Standard judging rubric"))
            
            # Default Users & Sessions
            org_user = User(id="usr_org", name="Alice Organizer", email="organizer@example.org", role="organizer")
            prt_user = User(id="usr_prt", name="Charlie Participant", email="participant@example.org", role="participant")
            jdg_user = User(id="usr_jdg_01", name="Dr. Evelyn Vance", email="judge1@example.org", role="judge")
            db_check.add_all([org_user, prt_user, jdg_user])
            db_check.commit()
            
            db_check.add_all([
                UserSession(id="org_7f2a", user_id=org_user.id),
                UserSession(id="prt_2e88", user_id=prt_user.id),
                UserSession(id="jdg_a_91bc", user_id=jdg_user.id),
                Judge(id="jdg_01", user_id=jdg_user.id, name="Dr. Evelyn Vance", email="judge1@example.org")
            ])
            db_check.commit()
    finally:
        db_check.close()
except Exception as e:
    print(f"Database table creation / auto-seed notice: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Offline Hackathon Submission & Isolated Judging Platform (Dogfood 2026)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration for offline React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Dogfood 2026 Hackathon Platform",
        "docs": "/docs",
        "gallery": "/api/projects",
        "results": "/api/results"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
