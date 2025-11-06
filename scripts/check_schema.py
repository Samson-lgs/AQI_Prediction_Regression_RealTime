import psycopg2
import os

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("\nPOLLUTION_DATA COLUMNS:")
print("-" * 50)
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'pollution_data' 
    ORDER BY ordinal_position;
""")
for row in cur.fetchall():
    print(f"{row[0]:25} {row[1]:20} nullable={row[2]}")

print("\n\nSAMPLE DATA (1 row):")
print("-" * 50)
cur.execute("SELECT * FROM pollution_data LIMIT 1;")
columns = [desc[0] for desc in cur.description]
row = cur.fetchone()
if row:
    for col, val in zip(columns, row):
        print(f"{col:25} {val}")
else:
    print("No data found")

conn.close()
