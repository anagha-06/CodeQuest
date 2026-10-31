from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():

    admin = Admin.query.filter_by(username="admin").first()

    if admin:
        admin.password = generate_password_hash("admin123")

    else:
        admin = Admin(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)

    db.session.commit()

    print("Admin password reset successfully!")