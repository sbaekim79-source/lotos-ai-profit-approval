from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


SQLALCHEMY_DATABASE_URL = settings.database_url
DB_PATH = settings.sqlite_path
if DB_PATH is not None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_sqlite_schema() -> None:
    if not settings.is_sqlite:
        return
    with engine.begin() as connection:
        internal_resource_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(internal_resource_rules)"))
        }
        if internal_resource_columns:
            additions = {
                "location_name": "VARCHAR",
                "vendor_name": "VARCHAR",
                "mandatory": "BOOLEAN NOT NULL DEFAULT 1",
            }
            for column_name, column_sql in additions.items():
                if column_name not in internal_resource_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE internal_resource_rules "
                            f"ADD COLUMN {column_name} {column_sql}"
                        )
                    )

        user_columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(users)"))
        }
        if user_columns:
            user_additions = {
                "hashed_password": "VARCHAR",
                "last_login_at": "DATETIME",
            }
            for column_name, column_sql in user_additions.items():
                if column_name not in user_columns:
                    connection.execute(
                        text(f"ALTER TABLE users ADD COLUMN {column_name} {column_sql}")
                    )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
