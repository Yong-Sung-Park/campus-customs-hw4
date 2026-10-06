"""Password hashing and signed session cookies.

Passwords: PBKDF2-HMAC-SHA256, 16-byte random salt, 120,000 iterations, stored
as ``pbkdf2_sha256$<salt>$<hex digest>``. This matches the seed users in
campus_customs.db, so the test account keeps working.

Sessions: an HttpOnly cookie holding ``<user_id>.<expires>.<signature>``,
signed with HMAC-SHA256 using SESSION_SECRET from .env. No session table is
needed, and a tampered or expired cookie is simply rejected.
"""

import hashlib
import hmac
import os
import re
import secrets
import time

from dotenv import load_dotenv
from fastapi import Request, Response

import db

load_dotenv(db.ROOT_DIR / ".env")

PBKDF2_ITERATIONS = 120_000
HASH_SCHEME = "pbkdf2_sha256"

SESSION_COOKIE = "cc_session"
SESSION_MAX_AGE = 7 * 24 * 3600  # one week

_SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not _SESSION_SECRET:
    # Still works without .env, but everyone is logged out when the server restarts.
    _SESSION_SECRET = secrets.token_urlsafe(48)
    print("WARNING: SESSION_SECRET not set in .env; using a temporary secret.")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


# ---------- passwords ----------

def _pbkdf2(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{HASH_SCHEME}${salt}${_pbkdf2(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt, digest = stored.split("$")
    except ValueError:
        return False
    if scheme != HASH_SCHEME:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt), digest)


# A real hash to check against when the email doesn't exist, so a failed
# login takes the same time whether or not the account is real.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- users ----------

def normalize_email(email: str) -> str:
    return email.strip().lower()


def public_user(row) -> dict:
    """The user fields that are safe to send to the browser or the agent."""
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return {
        "id": row["id"],
        "first_name": first,
        "last_name": last,
        "name": row["name"],
        "email": row["email"],
    }


def get_user_by_id(user_id: int) -> dict | None:
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row) if row else None


def authenticate(email: str, password: str) -> dict | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (normalize_email(email),)
        ).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return public_user(row)


class SignupError(ValueError):
    pass


def create_user(first_name: str, last_name: str, email: str, password: str) -> dict:
    first_name, last_name = first_name.strip(), last_name.strip()
    email = normalize_email(email)
    if not first_name or not last_name:
        raise SignupError("Please enter your first and last name.")
    if len(first_name) > 60 or len(last_name) > 60:
        raise SignupError("Names must be 60 characters or fewer.")
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise SignupError("Please enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SignupError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    with db.connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise SignupError("An account with that email already exists.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"{first_name} {last_name}", email, hash_password(password), first_name, last_name),
        )
        user_id = cur.lastrowid
    return get_user_by_id(user_id)


# ---------- sessions ----------

def _sign(payload: str) -> str:
    return hmac.new(_SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_MAX_AGE}"
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str) -> int | None:
    try:
        user_id, expires, sig = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(f"{user_id}.{expires}"), sig):
        return None
    if int(expires) < time.time():
        return None
    return int(user_id)


def set_session_cookie(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        make_session_token(user_id),
        max_age=SESSION_MAX_AGE,
        httponly=True,  # JavaScript can't read it, so XSS can't steal it
        samesite="lax",  # not sent on cross-site POSTs
        secure=False,  # local http dev server; set True behind HTTPS
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def current_user(request: Request) -> dict | None:
    """FastAPI dependency: the logged-in user, or None for guests."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    user_id = read_session_token(token)
    return get_user_by_id(user_id) if user_id is not None else None
