# Campus Customs Shop + Chatbot (Homework 4)

A customer website for **Campus Customs** (Yale apparel, 57 Broadway, New Haven) with an AI shopping assistant.

- **Front end:** React + Vite + TypeScript (`frontend/`): Home, Products (search / category / size-in-stock / sort), single-item pages, About Us, create account / log in, and a floating chat.
- **Back end:** Python FastAPI (`backend/main.py`) serving products, images, auth, and chat.
- **Agent:** PydanticAI on `gpt-5.6-luna` via Portkey. It looks up real prices and stock from SQLite, puts matching products on the page as cards, remembers logged-in shoppers, knows which product page you're on, and logs every step to an audit trail.

The full design doc is [`output/harness.md`](output/harness.md). Live test screenshots are in [`output/app_check.html`](output/app_check.html).

---

## 1. Get the data pack (not in git)

The database and product images are **not** committed. Unzip the course `data.zip` so you have:

```text
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # 102 .jpg files referenced by the catalogue table
```

## 2. Configure secrets

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Fill in `.env`:

| Key | What |
|---|---|
| `PORTKEY_API_KEY` | Your Portkey key (used for `gpt-5.6-luna`) |
| `SESSION_SECRET` | Any long random string. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |

## 3. Back end (FastAPI + agent)

```bash
# from hw4/
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

cd backend
uvicorn main:app --reload --port 8000
```

Check: <http://localhost:8000/api/health> returns `{"status":"ok"}`.

## 4. Front end (React + Vite)

```bash
# in a second terminal, from hw4/
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` and `/media` to the backend on port 8000, so both servers must be running.

## 5. Try it

- **Test account:** `test@campuscustoms.yale.edu` / `password` (from the seed database). You can also create a new account.
- In the chat (bottom right), try:
  - "What hoodies do you have?" (cards appear at the top of the page)
  - On a product page: "Is this in stock in M?" (honest stock; if it's sold out, similar in-stock items appear)
  - "Do you have this in pink?" on a product page (uses page context)
  - Log in, chat, refresh: your conversation comes back.

---

## Project layout

```text
hw4/
├── AI_prompts.md            # what I typed to my vibe coder, per problem
├── requirements.txt
├── .env.example             # placeholders only
├── .gitignore               # keeps out .env, data/, *.db, images, .venv, node_modules
├── README.md
├── frontend/                # Vite React TypeScript app
│   └── src/ (App, api.ts, auth.tsx, chat.tsx, components/, pages/)
├── backend/
│   ├── main.py              # FastAPI app: uvicorn main:app --reload --port 8000
│   ├── agent.py             # PydanticAI agent wiring, validators, agent loop
│   ├── tools.py             # agent tools (search, price, stock, alternatives, customer, page)
│   ├── models.py            # Pydantic types (API + tool results + agent output)
│   ├── prompts/prompt.md    # system prompt: voice, tools, honesty, safety
│   ├── db.py                # SQLite helpers (catalogue, search, chat history)
│   ├── auth.py              # password hashing + signed session cookie
│   └── audit.py             # append-only audit trail writer
└── output/
    ├── harness.md           # how the whole system works
    ├── design.md            # Problem 10 design write-up
    ├── usability.md         # Problem 9 improvements
    ├── app_check.html       # Problem 11 test report (open in a browser)
    ├── app_check_images/    # screenshots linked from app_check.html
    └── audit_trail.json     # agent-loop log (append-only)
```
