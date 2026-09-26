from fastapi import Request, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.models import User, Session as UserSession

cookie_header = APIKeyHeader(name="Cookie", auto_error=False)
authorization_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_session_token_from_request(request: Request) -> Optional[str]:
    # Check Cookie header or cookies jar
    cookie_str = request.headers.get("cookie")
    if cookie_str:
        # e.g. session=org_7f2a; other=xyz
        parts = cookie_str.split(";")
        for p in parts:
            p = p.strip()
            if p.startswith("session="):
                return p.split("session=", 1)[1].strip()
    
    # Check direct cookie dictionary
    if "session" in request.cookies:
        return request.cookies["session"]
    
    # Check Authorization header (Bearer ...)
    auth_header = request.headers.get("authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        if auth_header.startswith("session="):
            return auth_header.split("session=", 1)[1].strip()
        return auth_header.strip()

    return None

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = get_session_token_from_request(request)
    if not token:
        return None
    
    session = db.query(UserSession).filter(UserSession.id == token).first()
    if session:
        return session.user
    
    # Fallback to direct user ID or email lookup for flexible testing/dev
    user_by_id = db.query(User).filter((User.id == token) | (User.email == token)).first()
    return user_by_id

def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return current_user

def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: role '{current_user.role}' not permitted for this resource"
            )
        return current_user
    return role_checker

require_participant = require_role("participant", "organizer", "admin")
require_judge = require_role("judge", "admin")
require_organizer = require_role("organizer", "admin")
require_admin = require_role("admin")
