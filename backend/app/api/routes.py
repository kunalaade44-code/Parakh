from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_user_optional, require_role, require_judge, require_organizer, require_participant
from app.models.models import User, Session as UserSession, Event, Track, Team, Project, Judge, JudgeAssignment, Criterion, Score, Vote, Comment, AuditLog
from app.schemas.schemas import UserCreate, UserOut, LoginRequest, EventCreate, EventOut, TeamCreate, TeamOut, ProjectCreate, ProjectOut, ScoreSubmit, ScoreOut, JudgeOut, VoteCreate, CommentCreate, CommentOut
from app.services.judging_engine import calculate_project_results

router = APIRouter()

# ----------------- AUTH & SESSIONS -----------------
@router.post("/auth/register", response_model=UserOut)
def register(req: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        name=req.name,
        email=req.email,
        role=req.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/auth/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        # Create on demand if dev mode
        user = User(
            id=f"usr_{uuid.uuid4().hex[:8]}",
            name=req.email.split("@")[0].capitalize(),
            email=req.email,
            role="participant"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create session token
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    session = UserSession(id=session_id, user_id=user.id)
    db.add(session)
    db.commit()

    response.set_cookie(
        key="session",
        value=session_id,
        httponly=False,
        samesite="lax"
    )
    return {
        "session_id": session_id,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    judge_info = None
    if user.role == "judge":
        judge = db.query(Judge).filter(Judge.user_id == user.id).first()
        if judge:
            judge_info = {
                "id": judge.id,
                "name": judge.name,
                "tracks": [t.id for t in judge.tracks]
            }
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "judge": judge_info
    }

@router.post("/auth/logout")
def logout(response: Response, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()
    db.commit()
    response.delete_cookie("session")
    return {"message": "Logged out successfully"}

# ----------------- EVENTS (T1) -----------------
@router.get("/events")
def list_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    out = []
    for e in events:
        out.append({
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "submissions_close": e.submissions_close.isoformat(),
            "tracks": [{"id": t.id, "name": t.name} for t in e.tracks],
            "criteria": [{"id": c.id, "name": c.name, "weight": c.weight} for c in e.criteria]
        })
    return out

@router.get("/events/{event_id}")
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "id": event.id,
        "name": event.name,
        "description": event.description,
        "submissions_close": event.submissions_close.isoformat(),
        "tracks": [{"id": t.id, "name": t.name} for t in event.tracks],
        "criteria": [{"id": c.id, "name": c.name, "weight": c.weight} for c in event.criteria],
        "projects_count": len(db.query(Project).all())
    }

@router.post("/events", dependencies=[Depends(require_organizer)])
def create_event(req: EventCreate, db: Session = Depends(get_db)):
    event = Event(
        id=f"evt_{uuid.uuid4().hex[:8]}",
        name=req.name,
        description=req.description or "",
        submissions_close=req.submissions_close
    )
    db.add(event)
    db.commit()

    if req.tracks:
        for t in req.tracks:
            track = Track(id=f"trk_{uuid.uuid4().hex[:8]}", event_id=event.id, name=t.name)
            db.add(track)
    if req.criteria:
        for c in req.criteria:
            crit = Criterion(id=f"crt_{uuid.uuid4().hex[:8]}", event_id=event.id, name=c.name, weight=c.weight)
            db.add(crit)
    
    db.commit()
    db.refresh(event)
    return {"id": event.id, "name": event.name}

# ----------------- TEAMS (T1) -----------------
@router.post("/teams", dependencies=[Depends(require_participant)])
def create_team(req: TeamCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    event = db.query(Event).first()
    event_id = req.event_id or (event.id if event else "evt_01")
    team = Team(
        id=f"tm_{uuid.uuid4().hex[:8]}",
        event_id=event_id,
        name=req.name,
        invite_code=uuid.uuid4().hex[:8]
    )
    team.members.append(user)
    db.add(team)
    db.commit()
    db.refresh(team)
    return {
        "id": team.id,
        "name": team.name,
        "invite_code": team.invite_code,
        "invite_link": f"/teams/join/{team.invite_code}"
    }

@router.post("/teams/join/{invite_code}", dependencies=[Depends(require_participant)])
def join_team(invite_code: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.invite_code == invite_code).first()
    if not team:
        raise HTTPException(status_code=404, detail="Invalid team invite code")
    if user not in team.members:
        team.members.append(user)
        db.commit()
    return {"message": f"Successfully joined {team.name}", "team_id": team.id}

@router.get("/teams/my")
def get_my_teams(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [{
        "id": t.id,
        "name": t.name,
        "invite_code": t.invite_code,
        "members": [{"id": m.id, "name": m.name, "email": m.email} for m in t.members]
    } for t in user.teams]

# ----------------- PROJECTS & GALLERY (T1) -----------------
@router.get("/projects")
def get_gallery(
    track: str = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """
    Public Gallery. Publicly accessible without any authentication.
    Returns fixture and user projects with track info and stats.
    """
    query = db.query(Project)
    if track and track != "all":
        query = query.filter(Project.track_id == track)
    if search:
        s = f"%{search}%"
        query = query.filter((Project.title.ilike(s)) | (Project.summary.ilike(s)))
    
    projects = query.order_by(Project.submitted_at.desc()).all()
    
    out = []
    for p in projects:
        score_count = len(p.scores)
        avg_score = None
        if score_count > 0:
            total = 0
            cnt = 0
            for s in p.scores:
                try:
                    c_dict = json.loads(s.criteria_scores) if isinstance(s.criteria_scores, str) else s.criteria_scores
                    vals = list(c_dict.values())
                    if vals:
                        total += sum(vals) / len(vals)
                        cnt += 1
                except Exception:
                    pass
            if cnt > 0:
                avg_score = round(total / cnt, 2)

        out.append({
            "id": p.id,
            "title": p.title,
            "summary": p.summary,
            "repo_url": p.repo_url,
            "demo_url": p.demo_url,
            "track": {"id": p.track.id, "name": p.track.name} if p.track else None,
            "team": {"id": p.team.id, "name": p.team.name} if p.team else None,
            "submitted_at": p.submitted_at.isoformat(),
            "scores_count": score_count,
            "average_score": avg_score,
            "votes_count": len(p.votes)
        })
    return out

@router.get("/projects/{project_id}")
def get_project_details(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    comments = [{
        "id": c.id,
        "user_name": c.user.name if c.user else "Anonymous",
        "content": c.content,
        "created_at": c.created_at.isoformat()
    } for c in project.comments]

    return {
        "id": project.id,
        "title": project.title,
        "summary": project.summary,
        "repo_url": project.repo_url,
        "demo_url": project.demo_url,
        "track": {"id": project.track.id, "name": project.track.name} if project.track else None,
        "team": {"id": project.team.id, "name": project.team.name, "members": [{"name": m.name} for m in project.team.members]} if project.team else None,
        "submitted_at": project.submitted_at.isoformat(),
        "scores_count": len(project.scores),
        "votes_count": len(project.votes),
        "comments": comments
    }

@router.post("/projects", dependencies=[Depends(require_participant)])
@router.post("/projects/new", dependencies=[Depends(require_participant)])
def submit_project(
    req: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Project Submission with STRICT deadline check.
    If event deadline is passed, MUST return HTTP 4xx.
    """
    event = db.query(Event).first()
    if not event:
        raise HTTPException(status_code=400, detail="No active hackathon event found")
    
    # Enforce deadline check
    now = datetime.utcnow()
    if now > event.submissions_close:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Submissions closed on {event.submissions_close.isoformat()}."
        )

    # Determine team
    team_id = req.team_id
    if not team_id:
        # Check if user has team
        if user.teams:
            team_id = user.teams[0].id
        else:
            # Auto-create team for participant
            team = Team(
                id=f"tm_{uuid.uuid4().hex[:8]}",
                event_id=event.id,
                name=f"{user.name}'s Team",
                invite_code=uuid.uuid4().hex[:8]
            )
            team.members.append(user)
            db.add(team)
            db.commit()
            team_id = team.id

    track_id = req.track_id
    if not track_id and event.tracks:
        track_id = event.tracks[0].id

    project = Project(
        id=f"prj_{uuid.uuid4().hex[:8]}",
        team_id=team_id,
        track_id=track_id,
        title=req.title,
        summary=req.summary or "",
        repo_url=req.repo_url or "",
        demo_url=req.demo_url or "",
        submitted_at=now
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "title": project.title, "status": "submitted"}

# ----------------- TIER 2: JUDGING & ISOLATION -----------------
@router.get("/judge/scores")
def get_judge_scores(
    judge: str = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    CRITICAL ISOLATION RULE:
    1. Participant accessing this -> 403 Forbidden.
    2. Judge B accessing this with ?judge=judge_a or attempting to inspect Judge A -> 403 Forbidden.
    3. Returns ONLY authenticated judge's own scores.
    """
    if user.role not in ["judge", "admin", "organizer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only assigned judges and organizers can access judge scoreboards."
        )

    # If current user is a judge, find their judge record
    judge_profile = db.query(Judge).filter(Judge.user_id == user.id).first()
    
    # If a query parameter ?judge=... is provided
    if judge:
        # If user is a judge and query param does not match their own judge id/email/name -> FORBIDDEN!
        if user.role == "judge":
            if not judge_profile or (judge != judge_profile.id and judge != judge_profile.email and judge != user.id and judge != user.email):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Judges cannot access peer judge scores (Strict Backend Isolation)."
                )

    # For judge role, strictly restrict query to their own judge_id
    if user.role == "judge":
        if not judge_profile:
            return []
        scores = db.query(Score).filter(Score.judge_id == judge_profile.id).all()
    else:
        # Organizer or Admin
        if judge:
            scores = db.query(Score).filter(Score.judge_id == judge).all()
        else:
            scores = db.query(Score).all()

    out = []
    for s in scores:
        crit = json.loads(s.criteria_scores) if isinstance(s.criteria_scores, str) else s.criteria_scores
        out.append({
            "id": s.id,
            "judge_id": s.judge_id,
            "project_id": s.project_id,
            "project_title": s.project.title if s.project else "Unknown",
            "criteria": crit,
            "comment": s.comment,
            "submitted_at": s.submitted_at.isoformat()
        })
    return out

@router.get("/judge/assignments")
def get_judge_assignments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role not in ["judge", "admin"]:
        raise HTTPException(status_code=403, detail="Only judges can view assignments")
    
    judge_profile = db.query(Judge).filter(Judge.user_id == user.id).first()
    if not judge_profile:
        return []

    # Get tracks assigned to judge
    judge_track_ids = [t.id for t in judge_profile.tracks]
    
    # Projects in judge's tracks
    projects = db.query(Project).filter(Project.track_id.in_(judge_track_ids)).all() if judge_track_ids else db.query(Project).limit(10).all()
    
    # Get scores already submitted by this judge
    my_scores = {s.project_id: s for s in db.query(Score).filter(Score.judge_id == judge_profile.id).all()}

    out = []
    for p in projects:
        score_entry = my_scores.get(p.id)
        crit = json.loads(score_entry.criteria_scores) if (score_entry and isinstance(score_entry.criteria_scores, str)) else (score_entry.criteria_scores if score_entry else {})
        out.append({
            "project_id": p.id,
            "title": p.title,
            "summary": p.summary,
            "repo_url": p.repo_url,
            "demo_url": p.demo_url,
            "track": {"id": p.track.id, "name": p.track.name} if p.track else None,
            "team_name": p.team.name if p.team else "Unknown",
            "is_scored": score_entry is not None,
            "my_score": {
                "criteria": crit,
                "comment": score_entry.comment if score_entry else ""
            } if score_entry else None
        })
    return out

@router.post("/judge/scores")
def submit_judge_score(
    req: ScoreSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role not in ["judge", "admin"]:
        raise HTTPException(status_code=403, detail="Only judges can submit scores")
    
    judge_profile = db.query(Judge).filter(Judge.user_id == user.id).first()
    if not judge_profile:
        raise HTTPException(status_code=400, detail="Judge profile not found for user")

    # Check if project exists
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Upsert score
    existing = db.query(Score).filter(
        Score.judge_id == judge_profile.id,
        Score.project_id == req.project_id
    ).first()

    if existing:
        existing.criteria_scores = json.dumps(req.criteria)
        existing.comment = req.comment or ""
        existing.submitted_at = datetime.utcnow()
    else:
        score = Score(
            id=f"scr_{uuid.uuid4().hex[:8]}",
            judge_id=judge_profile.id,
            project_id=req.project_id,
            criteria_scores=json.dumps(req.criteria),
            comment=req.comment or ""
        )
        db.add(score)

    db.commit()
    return {"message": "Score saved successfully", "project_id": req.project_id}

# ----------------- ORGANIZER DASHBOARD & CSV (T2) -----------------
@router.get("/organizer/overview", dependencies=[Depends(require_organizer)])
def get_organizer_overview(db: Session = Depends(get_db)):
    event = db.query(Event).first()
    projects = db.query(Project).all()
    judges = db.query(Judge).all()
    scores = db.query(Score).all()

    # Progress stats
    total_projects = len(projects)
    total_judges = len(judges)
    total_reviews = len(scores)

    # Per-track stats
    tracks = db.query(Track).all()
    track_stats = []
    for t in tracks:
        p_count = len([p for p in projects if p.track_id == t.id])
        j_count = len(t.judges)
        track_stats.append({
            "track_id": t.id,
            "track_name": t.name,
            "projects_count": p_count,
            "judges_count": j_count
        })

    # Judge progress
    judge_progress = []
    for j in judges:
        j_scores = [s for s in scores if s.judge_id == j.id]
        judge_progress.append({
            "judge_id": j.id,
            "name": j.name,
            "email": j.email,
            "reviews_completed": len(j_scores)
        })

    return {
        "event_name": event.name if event else "Dogfood Hackathon 2026",
        "submissions_close": event.submissions_close.isoformat() if event else None,
        "total_projects": total_projects,
        "total_judges": total_judges,
        "total_reviews": total_reviews,
        "tracks": track_stats,
        "judge_progress": judge_progress
    }

@router.get("/results")
def get_results(db: Session = Depends(get_db)):
    event = db.query(Event).first()
    event_id = event.id if event else "evt_01"
    return calculate_project_results(db, event_id)

@router.get("/export.csv")
def export_csv(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    CSV Export for Organizer.
    Must return HTTP 200 with valid CSV content header and comma-separated text.
    """
    if user.role not in ["organizer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: CSV export is reserved for organizers."
        )

    event = db.query(Event).first()
    event_id = event.id if event else "evt_01"
    results = calculate_project_results(db, event_id)

    lines = ["rank,project_id,title,team,track,raw_score,normalized_score,reviews_count,repo_url"]
    for r in results:
        # sanitize title/team for CSV
        title = f'"{r["title"]}"' if "," in r["title"] else r["title"]
        team = f'"{r["team_name"]}"' if "," in r["team_name"] else r["team_name"]
        track = f'"{r["track_name"]}"' if "," in r["track_name"] else r["track_name"]
        lines.append(f'{r["rank"]},{r["project_id"]},{title},{team},{track},{r["raw_avg_score"]},{r["final_score"]},{r["reviews_count"]},{r["repo_url"]}')

    csv_data = "\n".join(lines)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dogfood_results.csv"}
    )

# ----------------- TIER 3: COMMUNITY VOTING & COMMENTS -----------------
@router.post("/community/vote")
def vote_project(
    req: VoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Vote).filter(Vote.project_id == req.project_id, Vote.user_id == user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"voted": False, "message": "Vote removed"}
    
    vote = Vote(
        id=f"vot_{uuid.uuid4().hex[:8]}",
        project_id=req.project_id,
        user_id=user.id
    )
    db.add(vote)
    db.commit()
    return {"voted": True, "message": "Vote cast"}

@router.post("/community/comment")
def add_comment(
    req: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comment = Comment(
        id=f"cmt_{uuid.uuid4().hex[:8]}",
        project_id=req.project_id,
        user_id=user.id,
        content=req.content
    )
    db.add(comment)
    db.commit()
    return {"id": comment.id, "content": comment.content, "user_name": user.name}
