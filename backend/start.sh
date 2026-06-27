#!/bin/sh
set -e

echo "Creating database tables..."
python -c "
from app.database import Base, engine
from app import models
Base.metadata.create_all(bind=engine)
print('Tables created.')
"

echo "Seeding initial admin user..."
python -c "
from app.database import SessionLocal
from app import models
from app.services.auth_service import hash_password
from sqlalchemy import select

with SessionLocal() as db:
    existing = db.execute(select(models.User).where(models.User.username == 'admin')).scalar_one_or_none()
    if existing is None:
        admin = models.User(
            username='admin',
            display_name='관리자',
            role='ADMIN',
            hashed_password=hash_password('admin1234'),
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print('Admin user created.')
    else:
        print('Admin user already exists.')
"

echo "Starting backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8010}"
