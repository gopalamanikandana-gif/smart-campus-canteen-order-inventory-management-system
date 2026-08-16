# Smart Campus Canteen Order & Inventory Management System

A secure, server-driven campus canteen application designed around **reliable order placement, inventory consistency, server-trusted pricing, role-based access control, and an AI-assisted software change loop**.

> **Tactive Internship Assessment Project**  
> Built with a deliberately small and understandable technology stack so the complete application can be run, demonstrated, and explained end-to-end.

---

## 🚀 Project Highlights

- Student registration, login and logout
- Live menu with categories, availability and stock
- Menu search
- Cart management with stock-aware quantities
- Reliable order placement
- Server-side price calculation
- Automatic inventory deduction after successful orders
- Student order history
- Student order cancellation with business-rule validation
- Inventory restoration after valid cancellation
- Separate admin dashboard
- Admin menu and inventory management
- Admin order-status management
- Role-based authorization
- Secure password hashing
- Automated backend test suite
- Deliberate failure / red-run evidence
- AI-driven implementation → test → failure → fix → retest workflow
- Render-ready deployment configuration

---

## 🎯 Problem Statement

Campus canteens often depend on manual inventory tracking and counter-based ordering. This can lead to:

- Students not knowing whether an item is actually available
- Orders exceeding available stock
- Stale or incorrect pricing
- Difficulty tracking previous orders
- Manual inventory updates
- Limited control over order status

This project provides a centralized system where ordering and inventory decisions are validated by the server and persisted in the database.

---

## 💡 Solution

The application follows a simple workflow:

```text
Student Login
     ↓
Browse / Search Menu
     ↓
Add Items to Cart
     ↓
Server-Side Validation
     ↓
Place Order
     ↓
Calculate Price from Database
     ↓
Update Inventory
     ↓
Track Order
```

For cancellation:

```text
Pending Order
     ↓
Ownership + Status + Time Validation
     ↓
Cancel Order
     ↓
Restore Inventory
```

The important business rules are enforced on the backend rather than relying on client-side JavaScript.

---

## ✨ Core Business Rules

### Authentication & Authorization
- Users must be authenticated for protected operations.
- Students and administrators have different permissions.
- Students cannot access administrative operations.

### Inventory
- Orders cannot exceed available stock.
- Unavailable or zero-stock items cannot be ordered.
- Successful orders reduce inventory.
- Invalid orders do not consume inventory.
- Valid cancellations restore the ordered quantity.

### Pricing
- The browser does not control the final order price.
- The backend retrieves the current menu price from the database at checkout.

### Cart & Orders
- Quantities must be valid.
- Cart quantities are constrained by available stock.
- Empty carts cannot be placed as orders.
- Students can view their own order history.

### Order Cancellation
- Only the student who placed an order can cancel it.
- Cancellation is allowed only while the order is pending and within the configured cancellation window.
- Once processing has started, cancellation is rejected.
- Inventory is restored after a successful cancellation.

---

## 🏗️ Architecture

The primary application uses a simple layered Flask architecture:

```text
┌─────────────────────────────────────┐
│        Browser / User Interface     │
│       HTML + Jinja + CSS + JS       │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│            Flask Application        │
│ Routes · Sessions · Authorization   │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│           Service Layer             │
│ Order · Pricing · Stock · Rules     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│       Flask-SQLAlchemy / ORM        │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│              SQLite                 │
│ Users · Menu · Orders · OrderItems  │
└─────────────────────────────────────┘
```

### Why this architecture?

The application deliberately avoids unnecessary infrastructure. Flask, SQLAlchemy and SQLite provide enough capability for the complete canteen workflow while keeping the business logic easy to understand and maintain.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python + Flask |
| ORM / Database Access | Flask-SQLAlchemy + SQLAlchemy |
| Database | SQLite |
| Frontend | HTML + Jinja + CSS + Vanilla JavaScript |
| Authentication | Flask session-based authentication |
| Password Security | Werkzeug password hashing |
| Testing | pytest |
| Production Server | Gunicorn |
| Deployment | Render |
| Version Control | Git + GitHub |

---

## 📁 Project Structure

```text
smart-campus-canteen/
│
├── app.py
├── config.py
├── models.py
├── seed.py
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile
├── render.yaml
│
├── services/
│   ├── __init__.py
│   └── order_service.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── menu.html
│   ├── cart.html
│   ├── orders.html
│   └── admin/
│       └── dashboard.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── tests/
│   ├── test_auth.py
│   ├── test_authorization.py
│   ├── test_cart.py
│   ├── test_menu.py
│   ├── test_orders.py
│   ├── test_order_cancellation.py
│   └── test_admin.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DESIGN.md
│   ├── USER_GUIDE.md
│   ├── AI_CHANGE_LOG.md
│   └── SUBMISSION_CHECKLIST.md
│
├── test-evidence/
│   ├── deliberate_red_run.txt
│   ├── final_green_run.txt
│   ├── stage3_attempt1_failures.txt
│   └── stage3_attempt2_final_green.txt
│
└── presentation/
    └── Smart_Campus_Canteen_Presentation.pptx
```

---

## 💻 Run Locally

### Requirements

- Python 3.10+
- Git
- VS Code recommended

### 1. Clone the repository

```bash
git clone https://github.com/gopalamanikandana-gif/smart-campus-canteen-order-inventory-management-system.git
cd smart-campus-canteen
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env`.

Windows:

```bash
copy .env.example .env
```

Example:

```env
SECRET_KEY=replace-with-a-long-random-secret
DATABASE_URL=sqlite:///canteen.db
PORT=5000
```

> Never commit `.env` or production secrets to GitHub.

### 5. Seed the database

```bash
python seed.py
```

### 6. Start the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 🔐 Demo Accounts

### Student

```text
Email:    student@canteen.local
Password: Student@123
```

### Admin

```text
Email:    admin@canteen.local
Password: Admin@123
```

These are demonstration credentials for the assessment environment. Change them before using the application with real users.

---

## 🧪 Testing

Run the backend test suite from the project root:

```bash
pytest -q
```

The test suite covers:

- Registration and authentication
- Login/logout
- Authorization
- Student/admin access control
- Menu visibility and search
- Cart behavior
- Quantity and stock validation
- Order placement
- Inventory deduction
- Database-controlled pricing
- Order history isolation
- Admin menu operations
- Admin order-status transitions
- Order cancellation
- Cancellation ownership
- Cancellation status rules
- Cancellation time-window rules
- Inventory restoration

### Test Evidence

The repository contains captured evidence for:

- Normal test execution
- Deliberate failing / red run
- AI change-loop attempt
- Final green run

See:

```text
test-evidence/
```

---

## 🤖 AI-Assisted Development

AI was used as an engineering assistant during development for:

- Code generation and refinement
- Test generation
- Edge-case identification
- Failure diagnosis
- Feature implementation
- Documentation assistance

The AI change loop follows:

```text
Requirement
    ↓
AI Implementation
    ↓
Run Existing Tests
    ↓
Detect Failure
    ↓
Investigate Root Cause
    ↓
Correct
    ↓
Retest
    ↓
Pass
```

The detailed evidence is available in:

```text
docs/AI_CHANGE_LOG.md
```

and the Stage 2 / Stage 3 evidence files under:

```text
docs/
test-evidence/
```

---

## 🔒 Security

The application includes:

- Werkzeug password hashing
- Session-based authentication
- Role-based authorization
- Protected admin routes
- Server-side validation
- Server-controlled pricing
- Inventory validation before order creation
- Ownership validation for student orders
- Environment-based secret configuration
- `.env` excluded from version control

The server remains the security boundary; client-side validation is treated only as a usability feature.

---

## 📊 Assessment Deliverables

The repository contains the main project and supporting assessment materials:

| Deliverable | Location |
|---|---|
| Source code | Project root |
| README | `README.md` |
| Automated tests | `tests/` |
| Test evidence | `test-evidence/` |
| AI change-loop evidence | `docs/AI_CHANGE_LOG.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Design | `docs/DESIGN.md` |
| User guide | `docs/USER_GUIDE.md` |
| Presentation | `presentation/` |

---

## 🎥 5-Minute Demo

**Watch the Smart Campus Canteen System Demo:**

[▶️ Watch the 5-Minute Demo](https://drive.google.com/file/d/1U1479AV6iKMUDNm_3KDpMjypCQUrPyXv/view?usp=drivesdk)

### Video structure

```text
0:00–2:00
Problem → Approach → Solution

2:00–5:00
Live Application Demonstration
```

### Live demo flow

```text
Student Login
     ↓
Browse / Search Menu
     ↓
Add Item to Cart
     ↓
Place Order
     ↓
Show Updated Inventory
     ↓
Cancel Pending Order
     ↓
Show Inventory Restoration
     ↓
Admin Dashboard
     ↓
Testing Evidence
     ↓
AI Change Loop
```

---

## 🚀 Deployment

The application is configured for deployment on Render.

Deployment files:

```text
Procfile
render.yaml
```

### Production start command

```bash
gunicorn app:app
```

### Render setup

1. Push the repository to GitHub.
2. Create a new Web Service on Render.
3. Connect the GitHub repository.
4. Use the Python runtime.
5. Build command:

```bash
pip install -r requirements.txt
```

6. Start command:

```bash
gunicorn app:app
```

7. Configure `SECRET_KEY` as an environment variable.
8. Deploy the service.

> SQLite is suitable for this assessment/demo deployment. For a production multi-instance system, a managed relational database would be a natural future improvement.

---

## 📌 Future Improvements

Possible production extensions include:

- PostgreSQL for persistent multi-instance deployment
- Payment gateway integration
- Email/SMS order notifications
- QR-based order pickup
- Advanced inventory analytics
- Role-specific audit logs
- Containerized deployment
- Cloud object storage for media
- More granular administrative permissions

---

## 👨‍💻 Project

**Smart Campus Canteen Order & Inventory Management System**

Built as a focused software-engineering assessment project with emphasis on **working functionality, reliable business rules, testability, security, and AI-assisted development**.
