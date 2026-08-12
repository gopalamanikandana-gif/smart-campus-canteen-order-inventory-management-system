from app.database import Base, engine, SessionLocal
from app.auth import hash_password
from app.models import User, MenuItem

Base.metadata.create_all(bind=engine)

db = SessionLocal()

if not db.query(User).filter(User.email == "admin@canteen.local").first():
    db.add(
        User(
            name="Canteen Admin",
            email="admin@canteen.local",
            password_hash=hash_password("Admin@123"),
            role="ADMIN",
        )
    )

if not db.query(User).filter(User.email == "student@canteen.local").first():
    db.add(
        User(
            name="Demo Student",
            email="student@canteen.local",
            password_hash=hash_password("Student@123"),
            role="STUDENT",
        )
    )

if db.query(MenuItem).count() == 0:
    db.add_all(
        [
            MenuItem(name="Veg Burger", description="Fresh vegetable burger", price=80, stock=20),
            MenuItem(name="Pizza Slice", description="Cheese pizza slice", price=120, stock=15),
            MenuItem(name="Sandwich", description="Grilled vegetable sandwich", price=60, stock=25),
            MenuItem(name="Coffee", description="Hot filter coffee", price=30, stock=50),
        ]
    )

db.commit()
db.close()
print("Seed complete.")
