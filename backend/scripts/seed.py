import json
import os
import sys
from datetime import datetime

# Adjust Python path so scripts can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.models import User, Session as UserSession, Event, Track, Team, Project, Judge, Criterion, Score

def seed_database(fixture_path="fixtures.json"):
    print(f"[*] Starting database seed from {fixture_path}...")
    
    # Ensure tables exist
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    if not os.path.exists(fixture_path):
        # Check parent folder
        parent_fixture = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), fixture_path)
        if os.path.exists(parent_fixture):
            fixture_path = parent_fixture
        else:
            print(f"[!] Fixture file not found at {fixture_path}")
            return

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # 1. Event
        evt_data = data.get("event", {})
        close_dt = datetime.fromisoformat(evt_data["submissions_close"].replace("Z", "+00:00")).replace(tzinfo=None)
        event = Event(
            id=evt_data.get("id", "evt_01"),
            name=evt_data.get("name", "Sample Hack 2026"),
            description="Official Dogfood 2026 Hackathon benchmark event.",
            submissions_close=close_dt
        )
        db.add(event)
        db.commit()

        # 2. Tracks
        track_map = {}
        for trk in data.get("tracks", []):
            track = Track(
                id=trk["id"],
                event_id=event.id,
                name=trk["name"]
            )
            db.add(track)
            track_map[trk["id"]] = track
        db.commit()

        # 3. Default Criteria
        default_criteria = [
            {"id": "crt_01", "name": "functionality", "weight": 0.35, "description": "Does it run and meet functional specs?"},
            {"id": "crt_02", "name": "quality", "weight": 0.35, "description": "Code quality, stability and design."},
            {"id": "crt_03", "name": "innovation", "weight": 0.30, "description": "Novelty and creative engineering."}
        ]
        for c in default_criteria:
            crit = Criterion(
                id=c["id"],
                event_id=event.id,
                name=c["name"],
                weight=c["weight"],
                description=c["description"]
            )
            db.add(crit)
        db.commit()

        # 4. Standard Pre-defined Test Users & Sessions for acceptance checks
        # Organizer
        org_user = User(
            id="usr_org",
            name="Alice Organizer",
            email="organizer@example.org",
            role="organizer"
        )
        db.add(org_user)
        db.commit()
        db.add(UserSession(id="org_7f2a", user_id=org_user.id))

        # Participant
        prt_user = User(
            id="usr_prt",
            name="Charlie Participant",
            email="participant@example.org",
            role="participant"
        )
        db.add(prt_user)
        db.commit()
        db.add(UserSession(id="prt_2e88", user_id=prt_user.id))

        # 5. Judges
        judges_data = data.get("judges", [])
        judge_map = {}
        for idx, j in enumerate(judges_data):
            j_user = User(
                id=f"usr_{j['id']}",
                name=j["name"],
                email=j["email"],
                role="judge"
            )
            db.add(j_user)
            db.commit()

            judge = Judge(
                id=j["id"],
                user_id=j_user.id,
                name=j["name"],
                email=j["email"]
            )
            for trk_id in j.get("tracks", []):
                if trk_id in track_map:
                    judge.tracks.append(track_map[trk_id])
            db.add(judge)
            judge_map[j["id"]] = judge

            # Map the first two judges to the test session tokens
            if idx == 0 or j["id"] == "jdg_01":
                db.add(UserSession(id="jdg_a_91bc", user_id=j_user.id))
            elif idx == 1 or j["id"] == "jdg_02":
                db.add(UserSession(id="jdg_b_44de", user_id=j_user.id))

        db.commit()

        # 6. Teams
        team_map = {}
        for tm in data.get("teams", []):
            team = Team(
                id=tm["id"],
                event_id=event.id,
                name=tm["name"],
                invite_code=f"inv_{tm['id']}"
            )
            db.add(team)
            # Add members
            for m_email in tm.get("members", []):
                member_user = db.query(User).filter(User.email == m_email).first()
                if not member_user:
                    member_user = User(
                        id=f"usr_{uuid.uuid4().hex[:8]}",
                        name=m_email.split("@")[0],
                        email=m_email,
                        role="participant"
                    )
                    db.add(member_user)
                    db.commit()
                team.members.append(member_user)
            team_map[tm["id"]] = team
        db.commit()

        # 7. Projects
        project_map = {}
        for prj in data.get("projects", []):
            sub_dt = datetime.fromisoformat(prj["submitted_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            project = Project(
                id=prj["id"],
                team_id=prj["team"],
                track_id=prj.get("track"),
                title=prj["title"],
                summary=prj.get("summary", ""),
                repo_url=prj.get("repo_url", ""),
                submitted_at=sub_dt
            )
            db.add(project)
            project_map[prj["id"]] = project
        db.commit()

        # 8. Scores
        for sc in data.get("scores", []):
            score = Score(
                id=f"scr_{uuid.uuid4().hex[:8]}",
                judge_id=sc["judge"],
                project_id=sc["project"],
                criteria_scores=json.dumps(sc.get("criteria", {})),
                comment=sc.get("comment", "")
            )
            db.add(score)
        db.commit()

        print("==================================================================")
        print("seeded. test logins:")
        print("  organizer    Cookie: session=org_7f2a")
        print("  judge_a      Cookie: session=jdg_a_91bc")
        print("  judge_b      Cookie: session=jdg_b_44de")
        print("  participant  Cookie: session=prt_2e88")
        print("==================================================================")

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    import uuid
    seed_database()
