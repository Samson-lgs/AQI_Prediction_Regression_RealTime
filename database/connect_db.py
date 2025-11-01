# Database Connection Module
# TODO: Implement database connection and CRUD operations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'aqi_prediction')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

# Connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_db_connection():
    """Create and return database connection"""
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

if __name__ == '__main__':
    conn = get_db_connection()
    if conn:
        print("Database connection successful!")
    else:
        print("Database connection failed!")
