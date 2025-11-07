import pandas as pd
from database.db_operations import get_db_connection

conn = get_db_connection()

# Get sample counts per city
query = """
SELECT city, COUNT(*) as total_samples 
FROM aqi_data 
GROUP BY city 
ORDER BY total_samples DESC 
LIMIT 10
"""
df = pd.read_sql(query, conn)
print("\n=== Top 10 Cities by Sample Count ===")
print(df)

# Check a specific city's data details
query2 = """
SELECT city, COUNT(*) as samples,
       MIN(timestamp) as earliest,
       MAX(timestamp) as latest,
       COUNT(DISTINCT DATE_TRUNC('hour', timestamp)) as distinct_hours
FROM aqi_data 
WHERE city = 'Ahmedabad'
GROUP BY city
"""
df2 = pd.read_sql(query2, conn)
print("\n=== Ahmedabad Data Details ===")
print(df2)

conn.close()
