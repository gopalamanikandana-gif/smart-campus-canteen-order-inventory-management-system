from werkzeug.security import generate_password_hash
from app import app
from models import db, User, MenuItem

def seed():
    with app.app_context():
        db.create_all()

        student = User.query.filter_by(email="student@canteen.local").first()
        if not student:
            db.session.add(User(
                name="Demo Student",
                email="student@canteen.local",
                password_hash=generate_password_hash("Student@123"),
                role="student"
            ))

        admin = User.query.filter_by(email="admin@canteen.local").first()
        if not admin:
            db.session.add(User(
                name="Canteen Admin",
                email="admin@canteen.local",
                password_hash=generate_password_hash("Admin@123"),
                role="admin"
            ))

        if MenuItem.query.count() == 0:
            db.session.add_all([
                MenuItem(name="Idli Sambar", description="Soft idlis served with fresh sambar.", category="Breakfast", price=35, stock=40),
                MenuItem(name="Masala Dosa", description="Crispy dosa with potato masala and chutney.", category="Breakfast", price=55, stock=35),
                MenuItem(name="Veg Fried Rice", description="Indo-Chinese fried rice with vegetables.", category="Lunch", price=80, stock=30),
                MenuItem(name="Paneer Wrap", description="Spiced paneer and vegetables in a soft wrap.", category="Snacks", price=70, stock=25),
                MenuItem(name="Fresh Lime Juice", description="Refreshing lime drink.", category="Beverages", price=30, stock=50),
                MenuItem(name="Tea", description="Hot campus-style tea.", category="Beverages", price=15, stock=60),
            ])

        db.session.commit()
        print("Database seeded successfully.")
        print("Student: student@canteen.local / Student@123")
        print("Admin:   admin@canteen.local / Admin@123")

if __name__ == "__main__":
    seed()
