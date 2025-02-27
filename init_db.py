from app import db, User
from werkzeug.security import generate_password_hash

# Create all tables
db.create_all()

# Create admin user
admin = User(username='admin', password=generate_password_hash('admin'))
db.session.add(admin)
db.session.commit()

print("Database initialized and admin user created!")
