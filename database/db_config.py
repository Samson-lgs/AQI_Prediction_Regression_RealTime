"""Database configuration settings"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database session generator"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()