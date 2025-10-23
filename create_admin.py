from app import app
from models.models import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(name='Admin', email='admin@example.com', password=generate_password_hash('password'), role='admin')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created')
    else:
        print('Admin user already exists')

# This script is for local setup; for production, run it manually or integrate into app startup if needed.
