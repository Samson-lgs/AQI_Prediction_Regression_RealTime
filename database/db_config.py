import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Iterator, Optional

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized PostgreSQL connection pool manager.

    Improvements:
    - ThreadedConnectionPool for multi-thread collectors.
    - Safe cursor context manager preventing double put/close.
    - Discards closed connections to avoid PoolError (unkeyed connection).
    - Simple health check.
    """

    _connection_pool: Optional[pool.AbstractConnectionPool] = None

    def __init__(self):
        if DatabaseManager._connection_pool is None:
            try:
                database_url = os.getenv('DATABASE_URL')
                if database_url:
                    result = urlparse(database_url)
                    db_config = {
                        'host': result.hostname,
                        'database': result.path[1:],
                        'user': result.username,
                        'password': result.password,
                        'port': result.port or 5432,
                        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '5'))
                    }
                    logger.info("Using DATABASE_URL for connection")
                else:
                    db_config = {
                        'host': os.getenv('DB_HOST', 'localhost'),
                        'database': os.getenv('DB_NAME', 'aqi_db'),
                        'user': os.getenv('DB_USER', 'postgres'),
                        'password': os.getenv('DB_PASSWORD'),
                        'port': int(os.getenv('DB_PORT', 5432)),
                        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '5'))
                    }
                    logger.info("Using individual DB environment variables")

                DatabaseManager._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=1,
                    maxconn=int(os.getenv('DB_POOL_MAX', '15')),
                    **db_config
                )
                logger.info("Database connection pool created successfully")
            except Exception as e:
                logger.error(f"Error creating connection pool: {e}")
                raise

    def get_connection(self):
        return DatabaseManager._connection_pool.getconn()

    def return_connection(self, connection):
        try:
            if connection is None:
                return
            if getattr(connection, 'closed', 0):
                logger.warning("Discarding closed DB connection; not returning to pool.")
                return
            DatabaseManager._connection_pool.putconn(connection)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")

    def execute_query(self, query, params=None):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall() if cursor.description else None
            connection.commit()
            return results
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)

    def execute_query_dicts(self, query, params=None):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall() if cursor.description else None
            connection.commit()
            return [dict(r) for r in results] if results is not None else None
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)

    @contextmanager
    def get_cursor(self, dicts: bool = False) -> Iterator:
        conn = self.get_connection()
        cur = None
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor if dicts else None)
            yield cur, conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Cursor operation failed: {e}")
            raise
        finally:
            if cur:
                cur.close()
            self.return_connection(conn)

    def health_check(self) -> bool:
        try:
            with self.get_cursor() as (cur, _):
                cur.execute("SELECT 1")
                _ = cur.fetchone()
            return True
        except Exception as e:
            logger.warning(f"DB health check failed: {e}")
            return False