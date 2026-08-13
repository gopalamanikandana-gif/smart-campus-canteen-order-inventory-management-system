# Smart Campus Canteen Order & Inventory Management System

A Flask + SQLite + SQLAlchemy campus canteen ordering and inventory application.

## Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
python app.py
```

Open http://127.0.0.1:5000

Demo accounts:
- Student: student@canteen.local / Student@123
- Admin: admin@canteen.local / Admin@123

For Render, use Gunicorn with `gunicorn app:app`.
