from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"
    expiresIn: int
    user: "UserOut"

class RefreshTokenRequest(BaseModel):
    refreshToken: str

class RoleOut(BaseModel):
    id: str
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)

class JurisdictionOut(BaseModel):
    id: str
    stateName: str
    districtName: str
    districtCode: str

    model_config = ConfigDict(from_attributes=True)

class UserOut(BaseModel):
    id: str
    username: str
    email: str
    fullName: str
    isActive: bool
    roles: List[str]
    jurisdictions: List[str]

    model_config = ConfigDict(from_attributes=True)

TokenResponse.model_rebuild()
