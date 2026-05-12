import psycopg2
from config import Config

conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
conn.autocommit = True
cur = conn.cursor()

cur.execute("DROP SCHEMA public CASCADE;")
cur.execute("CREATE SCHEMA public;")
cur.execute("GRANT ALL ON SCHEMA public TO postgres;")
cur.execute("GRANT ALL ON SCHEMA public TO public;")

print("Schema public dropped and recreated.")

cur.close()
conn.close()

from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
