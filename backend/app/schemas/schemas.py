from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "participant"

class UserCreate(UserBase):
    password: Optional[str] = None

class UserOut(UserBase):
    id: str
    created_at: datetime
    class Config:
        from_attributes = True

class SessionAuth(BaseModel):
    session_id: str
    user: UserOut

class LoginRequest(BaseModel):
    email: EmailStr
    password: Optional[str] = "password"

# Track Schemas
class TrackBase(BaseModel):
    name: str

class TrackCreate(TrackBase):
    pass

class TrackOut(TrackBase):
    id: str
    event_id: str
    class Config:
        from_attributes = True

# Criterion Schemas
class CriterionBase(BaseModel):
    name: str
    description: Optional[str] = ""
    weight: float = 1.0

class CriterionCreate(CriterionBase):
    pass

class CriterionOut(CriterionBase):
    id: str
    event_id: str
    class Config:
        from_attributes = True

# Event Schemas
class EventBase(BaseModel):
    name: str
    description: Optional[str] = ""
    submissions_close: datetime

class EventCreate(EventBase):
    tracks: Optional[List[TrackCreate]] = []
    criteria: Optional[List[CriterionCreate]] = []

class EventOut(EventBase):
    id: str
    created_at: datetime
    tracks: List[TrackOut] = []
    criteria: List[CriterionOut] = []
    class Config:
        from_attributes = True

# Team Schemas
class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    event_id: Optional[str] = None

class TeamOut(TeamBase):
    id: str
    event_id: str
    invite_code: str
    members: List[UserOut] = []
    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    title: str
    summary: Optional[str] = ""
    repo_url: Optional[str] = ""
    demo_url: Optional[str] = ""
    track_id: Optional[str] = None

class ProjectCreate(ProjectBase):
    team_id: Optional[str] = None

class ProjectOut(ProjectBase):
    id: str
    team_id: str
    submitted_at: datetime
    team: Optional[TeamOut] = None
    track: Optional[TrackOut] = None
    scores_count: Optional[int] = 0
    average_score: Optional[float] = None
    votes_count: Optional[int] = 0
    class Config:
        from_attributes = True

# Score Schemas
class ScoreSubmit(BaseModel):
    project_id: str
    criteria: Dict[str, float] # e.g. {"functionality": 4, "quality": 5}
    comment: Optional[str] = ""

class ScoreOut(BaseModel):
    id: str
    judge_id: str
    project_id: str
    criteria: Dict[str, float]
    comment: Optional[str] = ""
    submitted_at: datetime
    class Config:
        from_attributes = True

# Judge Schemas
class JudgeOut(BaseModel):
    id: str
    name: str
    email: str
    tracks: List[str] = []
    assignments_count: int = 0
    completed_count: int = 0

# Normalization & Results
class ProjectResult(BaseModel):
    project_id: str
    title: str
    team_name: str
    track_name: str
    repo_url: str
    submitted_at: datetime
    raw_avg_score: float
    z_score_normalized: float
    min_max_normalized: float
    final_score: float
    reviews_count: int
    community_votes: int = 0
    rank: int = 0

# Vote & Comment
class VoteCreate(BaseModel):
    project_id: str

class CommentCreate(BaseModel):
    project_id: str
    content: str

class CommentOut(BaseModel):
    id: str
    project_id: str
    user_name: str
    content: str
    created_at: datetime
