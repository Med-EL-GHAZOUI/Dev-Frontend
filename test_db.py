import psycopg2
try:
    conn = psycopg2.connect("host=localhost dbname=postgres user=postgres password=postgres")
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
