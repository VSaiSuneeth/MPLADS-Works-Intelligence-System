from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.core.security import decode_token, TokenPayload
from app.models.user import User

security_bearer = HTTPBearer(auto_error=False)

def get_current_token_payload(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> TokenPayload:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHENTICATED",
                    "message": "Authentication token missing or invalid",
                    "details": []
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials)
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "code": "INVALID_TOKEN",
                        "message": "Invalid token type",
                        "details": []
                    }
                }
            )
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_TOKEN",
                    "message": str(e),
                    "details": []
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db)
) -> User:
    user = db.query(User).filter(User.id == payload.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "Authenticated user record not found",
                    "details": []
                }
            }
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "error": {
                    "code": "USER_INACTIVE",
                    "message": "User account is inactive",
                    "details": []
                }
            }
        )
    return user

class RequireRole:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, payload: TokenPayload = Depends(get_current_token_payload)) -> TokenPayload:
        # ADMIN role has superuser access
        if "ADMIN" in payload.roles:
            return payload
            
        has_role = any(role in self.allowed_roles for role in payload.roles)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Operation requires one of the following roles: {', '.join(self.allowed_roles)}",
                        "details": []
                    }
                }
            )
        return payload

def verify_jurisdiction_access(jurisdiction_id: str, payload: TokenPayload = Depends(get_current_token_payload)) -> bool:
    # ADMIN role bypasses jurisdiction boundary
    if "ADMIN" in payload.roles:
        return True
        
    if jurisdiction_id not in payload.jurisdictions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "JURISDICTION_DENIED",
                    "message": "User is not authorized for the requested district jurisdiction",
                    "details": []
                }
            }
        )
    return True
