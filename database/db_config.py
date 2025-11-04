import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    _connection_pool = None

    def __init__(self):
        """Initialize database connection pool"""
        if DatabaseManager._connection_pool is None:
            try:
                DatabaseManager._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=os.getenv('DB_HOST', 'localhost'),
                    database=os.getenv('DB_NAME', 'aqi_db'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD'),
                    port=os.getenv('DB_PORT', 5432)
                )
                logger.info("Database connection pool created successfully")
            except Exception as e:
                logger.error(f"Error creating connection pool: {str(e)}")
                raise

    def get_connection(self):
        """Get a connection from the pool"""
        return DatabaseManager._connection_pool.getconn()

    def return_connection(self, connection):
        """Return a connection to the pool"""
        DatabaseManager._connection_pool.putconn(connection)

    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            
            # If the query returns results
            if cursor.description:
                results = cursor.fetchall()
            else:
                results = None
            
            connection.commit()
            return results

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise

        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)

    def execute_query_dicts(self, query, params=None):
        """Execute a query and return list of dicts (column names as keys)."""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)

            if cursor.description:
                results = cursor.fetchall()  # returns list of RealDictRow (dict-like)
            else:
                results = None

            connection.commit()
            # Convert to plain dicts for DataFrame compatibility
            return [dict(r) for r in results] if results is not None else None

        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise

        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)