import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL not set")
    exit(1)

def check():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'files';"))
        columns = [row[0] for row in result.fetchall()]
        print(f"Columns in 'files' table: {columns}")
        
        if 'description' in columns:
            print("SUCCESS: 'description' column exists.")
        else:
            print("FAILURE: 'description' column MISSING.")

if __name__ == "__main__":
    check()
