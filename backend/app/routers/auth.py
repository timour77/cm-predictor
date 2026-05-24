from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt

from app.models import LoginRequest, LoginResponse, RegisterRequest
from app.database import fetchone, execute
from app.utils.config import SECRET_KEY, ALGORITHM, JWT_EXPIRATION_HOURS

router = APIRouter()
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    try:
        return jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None


@router.post("/register", response_model=LoginResponse)
def register(body: RegisterRequest):
    if len(body.username) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(body.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters")

    existing = fetchone("SELECT id FROM users WHERE username = ?", (body.username,))
    if existing:
        raise HTTPException(400, "Username already taken")

    hashed = hash_password(body.password)
    user_id = execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (body.username, hashed),
    )
    token = create_token(user_id, body.username)
    return LoginResponse(user_id=user_id, token=token, username=body.username)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = fetchone("SELECT * FROM users WHERE username = ?", (body.username,))
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(401, "Invalid username or password")
    token = create_token(user["id"], user["username"])
    return LoginResponse(user_id=user["id"], token=token, username=user["username"])
