from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", String, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

judge_tracks = Table(
    "judge_tracks",
    Base.metadata,
    Column("judge_id", String, ForeignKey("judges.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", String, ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"usr_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="participant", nullable=False) # visitor, participant, judge, organizer, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    teams = relationship("Team", secondary=team_members, back_populates="members")
    judge_profile = relationship("Judge", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True) # session token (e.g. org_7f2a, jdg_a_91bc, or token string)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    submissions_close = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tracks = relationship("Track", back_populates="event", cascade="all, delete-orphan")
    criteria = relationship("Criterion", back_populates="event", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="event", cascade="all, delete-orphan")

class Track(Base):
    __tablename__ = "tracks"

    id = Column(String, primary_key=True, default=lambda: f"trk_{uuid.uuid4().hex[:8]}")
    event_id = Column(String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)

    event = relationship("Event", back_populates="tracks")
    projects = relationship("Project", back_populates="track")
    judges = relationship("Judge", secondary=judge_tracks, back_populates="tracks")

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=lambda: f"tm_{uuid.uuid4().hex[:8]}")
    event_id = Column(String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    invite_code = Column(String, unique=True, default=lambda: uuid.uuid4().hex[:10])
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="teams")
    members = relationship("User", secondary=team_members, back_populates="teams")
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: f"prj_{uuid.uuid4().hex[:8]}")
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    track_id = Column(String, ForeignKey("tracks.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    summary = Column(Text, default="")
    repo_url = Column(String, default="")
    demo_url = Column(String, default="")
    submitted_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="projects")
    track = relationship("Track", back_populates="projects")
    scores = relationship("Score", back_populates="project", cascade="all, delete-orphan")
    assignments = relationship("JudgeAssignment", back_populates="project", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="project", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="project", cascade="all, delete-orphan")

class Judge(Base):
    __tablename__ = "judges"

    id = Column(String, primary_key=True, default=lambda: f"jdg_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)

    user = relationship("User", back_populates="judge_profile")
    tracks = relationship("Track", secondary=judge_tracks, back_populates="judges")
    scores = relationship("Score", back_populates="judge", cascade="all, delete-orphan")
    assignments = relationship("JudgeAssignment", back_populates="judge", cascade="all, delete-orphan")

class JudgeAssignment(Base):
    __tablename__ = "judge_assignments"

    id = Column(String, primary_key=True, default=lambda: f"asg_{uuid.uuid4().hex[:8]}")
    judge_id = Column(String, ForeignKey("judges.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)

    judge = relationship("Judge", back_populates="assignments")
    project = relationship("Project", back_populates="assignments")

class Criterion(Base):
    __tablename__ = "criteria"

    id = Column(String, primary_key=True, default=lambda: f"crt_{uuid.uuid4().hex[:8]}")
    event_id = Column(String, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False) # e.g. functionality, quality, innovation, impact, presentation
    description = Column(Text, default="")
    weight = Column(Float, default=1.0) # Weight fraction (e.g. 0.35, 0.35, 0.30)

    event = relationship("Event", back_populates="criteria")

class Score(Base):
    __tablename__ = "scores"

    id = Column(String, primary_key=True, default=lambda: f"scr_{uuid.uuid4().hex[:8]}")
    judge_id = Column(String, ForeignKey("judges.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    criteria_scores = Column(Text, default="{}") # JSON string containing {"functionality": 4, "quality": 5, ...}
    comment = Column(Text, default="")
    submitted_at = Column(DateTime, default=datetime.utcnow)

    judge = relationship("Judge", back_populates="scores")
    project = relationship("Project", back_populates="scores")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(String, primary_key=True, default=lambda: f"vot_{uuid.uuid4().hex[:8]}")
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="votes")
    user = relationship("User", back_populates="votes")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=lambda: f"cmt_{uuid.uuid4().hex[:8]}")
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="comments")
    user = relationship("User", back_populates="comments")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:8]}")
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=datetime.utcnow)
