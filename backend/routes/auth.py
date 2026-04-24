from fastapi import APIRouter, HTTPException, status, Depends, Header, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from email.message import EmailMessage
import hashlib
import json
import re
import secrets
import smtplib
import urllib.parse
import urllib.request
import uuid

from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
password_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None

class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirmRequest(BaseModel):
    token: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserRecord(BaseModel):
    id: str
    username: str
    display_name: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    provider: str = "password"
    provider_id: Optional[str] = None
    password_reset_token_hash: Optional[str] = None
    password_reset_expires_at: Optional[str] = None
    created_at: str
    updated_at: str

class UserDatabase(BaseModel):
    users: list[UserRecord] = []

def public_user(user: UserRecord) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "email": user.email,
        "provider": user.provider,
    }

def load_users() -> UserDatabase:
    ensure_users_file_parent()
    if settings.users_file.exists():
        with open(settings.users_file, "r", encoding="utf-8") as f:
            return UserDatabase(**json.load(f))
    db = UserDatabase()
    save_users(db)
    return db

def save_users(db: UserDatabase):
    ensure_users_file_parent()
    with open(settings.users_file, "w", encoding="utf-8") as f:
        json.dump(db.model_dump(), f, ensure_ascii=False, indent=2)

def ensure_users_file_parent():
    settings.users_file.parent.mkdir(parents=True, exist_ok=True)

def normalize_username(username: str) -> str:
    normalized = (username or "").strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-32 characters and contain only letters, numbers, _ or -",
        )
    return normalized

def username_from_email(email: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", (email or "user").split("@")[0]).strip("-").lower()
    if len(base) < 3:
        base = f"user-{base}".strip("-")
    return base[:24]

def unique_username(db: UserDatabase, desired: str) -> str:
    base = normalize_username(desired)
    existing = {user.username for user in db.users}
    if base not in existing:
        return base

    for index in range(2, 1000):
        candidate = f"{base[:26]}-{index}"
        if candidate not in existing:
            return candidate

    return f"user-{uuid.uuid4().hex[:10]}"

def find_user_by_username(db: UserDatabase, username: str) -> Optional[UserRecord]:
    normalized = (username or "").strip().lower()
    return next((user for user in db.users if user.username == normalized), None)

def find_user_by_id(db: UserDatabase, user_id: str) -> Optional[UserRecord]:
    return next((user for user in db.users if user.id == user_id), None)

def find_user_by_provider(db: UserDatabase, provider: str, provider_id: str) -> Optional[UserRecord]:
    return next(
        (
            user for user in db.users
            if user.provider == provider and user.provider_id == provider_id
        ),
        None,
    )

def find_user_by_email(db: UserDatabase, email: Optional[str]) -> Optional[UserRecord]:
    if not email:
        return None
    normalized = email.lower()
    return next((user for user in db.users if user.email and user.email.lower() == normalized), None)

def normalize_email(email: Optional[str]) -> str:
    normalized = (email or "").strip().lower()
    if not normalized or "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Valid email is required")
    return normalized

def password_reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def app_base_url(request: Request) -> str:
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    return str(request.base_url).rstrip("/")

def send_password_reset_email(to_email: str, reset_link: str):
    if not settings.smtp_host or not settings.smtp_from_email:
        return False

    message = EmailMessage()
    message["Subject"] = "Сброс пароля в книге рецептов"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(
        "Здравствуйте!\n\n"
        "Чтобы сбросить пароль, откройте ссылку ниже:\n\n"
        f"{reset_link}\n\n"
        f"Ссылка действует {settings.password_reset_expire_minutes} минут.\n"
        "Если вы не запрашивали сброс пароля, просто проигнорируйте это письмо.\n"
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

    return True

def create_password_user(db: UserDatabase, request: RegisterRequest) -> UserRecord:
    username = normalize_username(request.username)
    if find_user_by_username(db, username):
        raise HTTPException(status_code=409, detail="Username already exists")

    email = normalize_email(request.email) if request.email else None
    if email and find_user_by_email(db, email):
        raise HTTPException(status_code=409, detail="Email already exists")

    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    now = datetime.utcnow().isoformat()
    user = UserRecord(
        id=f"user_{uuid.uuid4().hex[:12]}",
        username=username,
        display_name=(request.display_name or username).strip() or username,
        email=email,
        password_hash=password_context.hash(request.password),
        provider="password",
        created_at=now,
        updated_at=now,
    )
    db.users.append(user)
    save_users(db)
    return user

def ensure_admin_user() -> UserRecord:
    db = load_users()
    username = normalize_username(settings.admin_username)
    existing = find_user_by_username(db, username)
    if existing:
        return existing

    now = datetime.utcnow().isoformat()
    user = UserRecord(
        id="user_admin",
        username=username,
        display_name=username,
        password_hash=password_context.hash(settings.admin_password),
        provider="password",
        created_at=now,
        updated_at=now,
    )
    db.users.append(user)
    save_users(db)
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def token_for_user(user: UserRecord) -> str:
    return create_access_token(data={"sub": user.id, "username": user.username})

async def verify_token(authorization: str = Header(None)) -> UserRecord:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")

        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        user = find_user_by_id(load_users(), user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

async def optional_verify_token(authorization: str = Header(None)) -> Optional[UserRecord]:
    if not authorization:
        return None
    return await verify_token(authorization)

@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest):
    user = create_password_user(load_users(), request)
    access_token = token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer", "user": public_user(user)}

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    ensure_admin_user()
    db = load_users()
    user = find_user_by_username(db, request.username)

    if not user or not user.password_hash or not password_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if password_context.needs_update(user.password_hash):
        user.password_hash = password_context.hash(request.password)
        user.updated_at = datetime.utcnow().isoformat()
        save_users(db)

    return {"access_token": token_for_user(user), "token_type": "bearer", "user": public_user(user)}

@router.get("/verify")
async def verify(user: UserRecord = Depends(verify_token)):
    return {"user": public_user(user), "status": "valid"}

@router.get("/me")
async def me(user: UserRecord = Depends(verify_token)):
    return {"user": public_user(user)}

@router.patch("/me")
async def update_me(
    request: ProfileUpdateRequest,
    user: UserRecord = Depends(verify_token),
):
    db = load_users()
    existing = find_user_by_id(db, user.id)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    email = normalize_email(request.email) if request.email else ""
    if email:
        email_owner = find_user_by_email(db, email)
        if email_owner and email_owner.id != existing.id:
            raise HTTPException(status_code=409, detail="Email already exists")
        existing.email = email
    else:
        existing.email = None

    if request.display_name is not None:
        display_name = request.display_name.strip()
        existing.display_name = display_name or existing.username

    existing.updated_at = datetime.utcnow().isoformat()
    save_users(db)
    return {"user": public_user(existing)}

@router.post("/password/forgot")
async def request_password_reset(request_data: PasswordResetRequest, request: Request):
    email = normalize_email(request_data.email)
    db = load_users()
    user = find_user_by_email(db, email)
    dev_reset_link = None
    email_sent = False

    if user:
        token = secrets.token_urlsafe(32)
        user.password_reset_token_hash = password_reset_token_hash(token)
        user.password_reset_expires_at = (
            datetime.utcnow() + timedelta(minutes=settings.password_reset_expire_minutes)
        ).isoformat()
        user.updated_at = datetime.utcnow().isoformat()
        save_users(db)

        reset_link = f"{app_base_url(request)}/admin/reset-password.html?token={urllib.parse.quote(token)}"
        email_sent = send_password_reset_email(email, reset_link)
        if not email_sent and settings.debug:
            dev_reset_link = reset_link

    response = {
        "message": "If an account exists for this email, password reset instructions have been sent.",
        "email_sent": email_sent,
    }
    if dev_reset_link:
        response["dev_reset_link"] = dev_reset_link
    return response

@router.post("/password/reset")
async def reset_password(request: PasswordResetConfirmRequest):
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    token_hash = password_reset_token_hash(request.token)
    db = load_users()
    user = next(
        (item for item in db.users if item.password_reset_token_hash == token_hash),
        None,
    )

    if not user or not user.password_reset_expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    try:
        expires_at = datetime.fromisoformat(user.password_reset_expires_at)
    except ValueError:
        expires_at = datetime.utcnow() - timedelta(seconds=1)

    if expires_at < datetime.utcnow():
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        save_users(db)
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user.password_hash = password_context.hash(request.password)
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    user.updated_at = datetime.utcnow().isoformat()
    save_users(db)
    return {"message": "Password has been reset"}

def oauth_redirect_uri(request: Request, provider: str) -> str:
    base = settings.public_base_url.rstrip("/") if settings.public_base_url else str(request.base_url).rstrip("/")
    return f"{base}/api/auth/oauth/{provider}/callback"

def require_oauth_config(provider: str) -> tuple[str, str]:
    if provider == "google":
        client_id = settings.google_client_id
        client_secret = settings.google_client_secret
    elif provider == "facebook":
        client_id = settings.facebook_client_id
        client_secret = settings.facebook_client_secret
    else:
        raise HTTPException(status_code=404, detail="Unknown OAuth provider")

    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail=f"{provider.title()} OAuth is not configured")
    return client_id, client_secret

@router.get("/oauth/{provider}/start")
async def oauth_start(provider: str, request: Request):
    client_id, _ = require_oauth_config(provider)
    state = create_access_token(
        {"provider": provider, "kind": "oauth_state"},
        expires_delta=timedelta(minutes=10),
    )
    redirect_uri = oauth_redirect_uri(request, provider)

    if provider == "google":
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    elif provider == "facebook":
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "email,public_profile",
            "state": state,
        }
        url = f"https://www.facebook.com/v19.0/dialog/oauth?{urllib.parse.urlencode(params)}"
    else:
        raise HTTPException(status_code=404, detail="Unknown OAuth provider")

    return RedirectResponse(url)

def post_form(url: str, data: dict) -> dict:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def get_json(url: str, params: dict) -> dict:
    request = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def create_or_link_oauth_user(provider: str, profile: dict) -> UserRecord:
    provider_id = str(profile.get("id") or profile.get("sub") or "")
    if not provider_id:
        raise HTTPException(status_code=400, detail="OAuth profile did not include an id")

    db = load_users()
    existing = find_user_by_provider(db, provider, provider_id)
    if existing:
        return existing

    email = profile.get("email")
    existing_email = find_user_by_email(db, email)
    if existing_email:
        existing_email.provider = provider
        existing_email.provider_id = provider_id
        existing_email.updated_at = datetime.utcnow().isoformat()
        save_users(db)
        return existing_email

    desired_username = username_from_email(email or profile.get("name") or provider)
    username = unique_username(db, desired_username)
    now = datetime.utcnow().isoformat()
    user = UserRecord(
        id=f"user_{uuid.uuid4().hex[:12]}",
        username=username,
        display_name=(profile.get("name") or username).strip(),
        email=email.lower() if email else None,
        provider=provider,
        provider_id=provider_id,
        created_at=now,
        updated_at=now,
    )
    db.users.append(user)
    save_users(db)
    return user

@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, code: str, state: str):
    _, client_secret = require_oauth_config(provider)
    client_id, _ = require_oauth_config(provider)

    try:
        payload = jwt.decode(state, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("provider") != provider or payload.get("kind") != "oauth_state":
            raise HTTPException(status_code=400, detail="Invalid OAuth state")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_uri = oauth_redirect_uri(request, provider)

    if provider == "google":
        token = post_form("https://oauth2.googleapis.com/token", {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        })
        profile = get_json("https://openidconnect.googleapis.com/v1/userinfo", {
            "access_token": token["access_token"],
        })
    elif provider == "facebook":
        token = get_json("https://graph.facebook.com/v19.0/oauth/access_token", {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        })
        profile = get_json("https://graph.facebook.com/me", {
            "fields": "id,name,email",
            "access_token": token["access_token"],
        })
    else:
        raise HTTPException(status_code=404, detail="Unknown OAuth provider")

    user = create_or_link_oauth_user(provider, profile)
    token = token_for_user(user)
    return RedirectResponse(f"/admin/login.html?token={urllib.parse.quote(token)}")

@router.get("/users/{username}")
async def get_public_user(username: str):
    ensure_admin_user()
    user = find_user_by_username(load_users(), username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": public_user(user)}
