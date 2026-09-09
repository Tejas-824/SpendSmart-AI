# TokenWise

A small chat app that thinks about cost before it thinks about your question.

Every question you ask gets classified as simple or complex. Simple questions
go to a small, cheap model. Complex ones go to a bigger model - unless
today's spending limit is already used up, in which case everything gets
downgraded automatically. Repeated questions are served from a cache instead
of calling the model again. Every request is logged so you can see exactly
what it cost.

## How it works

1. You ask a question in the chat.
2. **Cache check** - if you (or anyone) asked this exact question before, you
   get the saved answer instantly, no model call, no cost.
3. **Routing** - the question is scored: short and simple → small model,
   long or asking for explanation/comparison/writing → big model.
4. **Budget guard** - if today's estimated spend has hit the daily limit, the
   request is forced onto the small model regardless of step 3.
5. The answer comes back with a badge showing which model handled it, how
   many tokens it used, and what it cost.
6. The Stats page shows totals: requests, tokens, cost, cache savings, and
   today's budget usage.

## Stack

- **Backend:** FastAPI, SQLite, JWT auth, [Groq](https://console.groq.com) for
  the actual LLM calls (free tier)
- **Frontend:** React + Vite, plain CSS, React Router

## Running it locally

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill it in:

```bash
cp .env.example .env
```

You need three things in `.env`:

- `GROQ_API_KEY` - get a free one at https://console.groq.com
- `AUTH_PASSWORD_HASH` - generate it by running:
  ```bash
  python generate_password_hash.py
  ```
  It'll ask you to type a password and print a line to paste into `.env`.
- `JWT_SECRET` - any long random string (e.g. run `python -c "import secrets; print(secrets.token_hex(32))"`)

Then start the server:

```bash
uvicorn main:app --reload
```

It runs at `http://localhost:8000`. Check `http://localhost:8000/docs` for the
interactive API docs FastAPI generates for you automatically.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

It runs at `http://localhost:5173`. Log in with the username from your
backend `.env` (default `admin`) and the password you chose when generating
the hash.

