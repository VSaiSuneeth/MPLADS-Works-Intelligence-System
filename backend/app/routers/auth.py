from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db.session import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest, UserOut
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid username or password",
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
                    "message": "User account is disabled",
                    "details": []
                }
            }
        )

    roles = [r.code for r in user.roles]
    jurisdictions = [j.id for j in user.jurisdictions]

    access_token = create_access_token(
        subject=user.id,
        username=user.username,
        roles=roles,
        jurisdictions=jurisdictions
    )
    refresh_token = create_refresh_token(
        subject=user.id,
        username=user.username
    )

    user_out = UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        fullName=user.full_name,
        isActive=user.is_active,
        roles=roles,
        jurisdictions=jurisdictions
    )

    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        expiresIn=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_out
    )

@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(request.refreshToken)
        if payload.type != "refresh":
            raise ValueError("Token is not a refresh token")
        
        user = db.query(User).filter(User.id == payload.sub).first()
        if not user or not user.is_active:
            raise ValueError("User not active or not found")
        
        roles = [r.code for r in user.roles]
        jurisdictions = [j.id for j in user.jurisdictions]

        new_access_token = create_access_token(
            subject=user.id,
            username=user.username,
            roles=roles,
            jurisdictions=jurisdictions
        )
        new_refresh_token = create_refresh_token(
            subject=user.id,
            username=user.username
        )

        return {
            "accessToken": new_access_token,
            "refreshToken": new_refresh_token,
            "expiresIn": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": str(e),
                    "details": []
                }
            }
        )

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    roles = [r.code for r in current_user.roles]
    jurisdictions = [j.id for j in current_user.jurisdictions]
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        fullName=current_user.full_name,
        isActive=current_user.is_active,
        roles=roles,
        jurisdictions=jurisdictions
    )
