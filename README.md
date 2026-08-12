# Smart Campus Canteen Order & Inventory Management System

A one-week internship assessment project designed around reliable order placement,
inventory validation, automated testing, deliberate failure detection, and an AI
change loop.

## Core functionality

A student can:
- register/login
- view available menu items
- add items to a cart
- place an order
- view their own orders

The backend enforces:
- authentication
- role-based authorization
- canteen operating hours
- positive quantity validation
- maximum quantity per item
- stock availability
- backend-side price calculation
- atomic order + inventory updates

An admin can:
- view all orders
- add menu items
- update menu item stock/availability
- update order status

## Stack

- Frontend: React + Vite
- Backend: FastAPI
- Database: SQLite + SQLAlchemy
- Authentication: JWT
- Password hashing: Werkzeug
- Backend tests: pytest
- E2E tests: Playwright

## Requirements

- Python 3.10+
- Node.js 18+
- npm
- Git

## 1. Run backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux

python seed.py
uvicorn app.main:app --reload --port 8000
```

Backend:
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs

## 2. Run frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:
http://localhost:5173

## Demo accounts

After `python seed.py`:

- Admin: `admin@canteen.local` / `Admin@123`
- Student: `student@canteen.local` / `Student@123`

Change these credentials before any public deployment.

## 3. Run backend tests

From `backend`:

```bash
pytest -q
```

Expected baseline: all tests pass.

## 4. Run frontend E2E tests

Start both backend and frontend first.

From `frontend`:

```bash
npm install
npx playwright install
npm run test:e2e
```

## Deliberate red run

The assessment requires a real failing test run.

1. Run `pytest -q` and save the green output.
2. In `backend/app/services/order_service.py`, temporarily change:

```python
subtotal = item.price * quantity
```

to:

```python
subtotal = item.price + quantity
```

3. Run:

```bash
pytest -q
```

4. Capture the failing output as `docs/evidence/red-run.txt`.
5. Restore the correct multiplication.
6. Run tests again and capture the final green output.

Do NOT leave the deliberate bug in the submitted repository.

## AI change loop

After the baseline is complete, use an AI coding agent to implement this new feature:

> Add order cancellation for PENDING orders. When a student cancels a pending
> order, restore the ordered quantities to inventory. Cancellation must be
> rejected once the order is PREPARING, READY, or COMPLETED. Add automated tests
> for successful cancellation, invalid status cancellation, unauthorized
> cancellation, and inventory restoration.

Record:
- exact prompt
- files changed
- tests before/after
- failures
- AI diagnosis
- corrections
- number of attempts
- any manual intervention

See `docs/AI_CHANGE_LOG.md`.

## Security checklist

- Never commit `.env`
- Use `.env.example` only as a template
- Passwords are hashed
- JWT is required for protected routes
- Admin routes require ADMIN role
- Prices are read from the database
- Input is validated with Pydantic
- Inventory updates happen inside a database transaction
- CORS is restricted by configuration

## Submission checklist

See `docs/SUBMISSION_CHECKLIST.md`.
