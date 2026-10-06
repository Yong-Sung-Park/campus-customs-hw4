"""Campus Customs API.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import logging
import time
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent
import auth
import db
from models import ChatReply, ChatRequest, ChatTurn

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")

# The Vite dev server proxies /api and /media, so CORS is only a fallback
# for calling the API directly from another local port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.mount("/media/products", StaticFiles(directory=db.PRODUCTS_DIR), name="product-images")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict]:
    return db.list_products()


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    product = db.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------- auth ----------

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup")
def signup(req: SignupRequest, response: Response) -> dict:
    try:
        user = auth.create_user(req.first_name, req.last_name, req.email, req.password)
    except auth.SignupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    auth.set_session_cookie(response, user["id"])
    return {"user": user}


@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response) -> dict:
    user = auth.authenticate(req.email, req.password)
    if user is None:
        # Same message whether the email or the password was wrong.
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    auth.set_session_cookie(response, user["id"])
    return {"user": user}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict:
    auth.clear_session_cookie(response)
    return {"ok": True}


@app.get("/api/me")
def me(user: dict | None = Depends(auth.current_user)) -> dict:
    return {"user": user}


# ---------- chat ----------

# Simple in-memory rate limit so nobody can spam the paid model:
# at most CHAT_LIMIT messages per CHAT_WINDOW seconds per visitor (user id, else IP).
CHAT_LIMIT = 15
CHAT_WINDOW = 60
_recent_chats: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str) -> None:
    now = time.monotonic()
    q = _recent_chats[key]
    while q and now - q[0] > CHAT_WINDOW:
        q.popleft()
    if len(q) >= CHAT_LIMIT:
        raise HTTPException(status_code=429, detail="Whoa, that's a lot of questions! Please wait a minute and try again.")
    q.append(now)


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request, user: dict | None = Depends(auth.current_user)) -> ChatReply:
    check_rate_limit(f"user:{user['id']}" if user else f"ip:{request.client.host if request.client else 'unknown'}")
    message = req.message.strip()
    # Logged-in shoppers: the saved conversation is the source of truth.
    # Guests: use the recent turns the widget sent (nothing is stored).
    if user:
        history = [ChatTurn(role=m["role"], content=m["content"]) for m in db.load_chat_history(user["id"], limit=12)]
    else:
        history = req.history
    try:
        reply = await agent.run_chat(message, history, user=user, page=req.page)
    except agent.AgentNotConfigured as e:
        log.error("Chat agent not configured: %s", e)
        raise HTTPException(status_code=503, detail="The shop assistant isn't set up yet. Please try again later.")
    except Exception:
        log.exception("Chat agent failed")
        raise HTTPException(
            status_code=502,
            detail="Sorry, I hit a snag answering that. Please try again in a moment.",
        )
    if user:
        db.save_chat_message(user["id"], "user", message)
        db.save_chat_message(user["id"], "assistant", reply.reply, [c.model_dump() for c in reply.products])
    return reply


@app.get("/api/chat/history")
def chat_history(user: dict | None = Depends(auth.current_user)) -> dict:
    """Saved conversation for the logged-in shopper (empty for guests)."""
    if not user:
        return {"messages": []}
    return {"messages": db.load_chat_history(user["id"], limit=50)}
