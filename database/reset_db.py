import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to default database
conn = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="postgres123",
    database="postgres"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Drop and create database
cursor = conn.cursor()
cursor.execute("DROP DATABASE IF EXISTS aqi_db")
cursor.execute("CREATE DATABASE aqi_db")

cursor.close()
conn.close()

print("Database dropped and recreated successfully!")