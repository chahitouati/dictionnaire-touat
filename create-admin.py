
from app import app, db
from database.models import User
from werkzeug.security import generate_password_hash
with app.app_context():
    admin = User(
        username='admin',
        email='admin@touat.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        region='توات'
    )
    db.session.add(admin)
    db.session.commit()
    print('✅ Admin créé')