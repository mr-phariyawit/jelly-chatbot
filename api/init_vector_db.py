
import os
import sqlalchemy
from sqlalchemy import text
from google.cloud.sql.connector import Connector, IPTypes
from dotenv import load_dotenv

load_dotenv()

def init_vector_extension():
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")

    if not all([instance_connection_name, db_user, db_pass, db_name]):
        print("Error: Missing database credentials in environment variables.")
        return

    print(f"Connecting to {instance_connection_name}...")
    
    # Initialize Cloud SQL Connector
    connector = Connector()

    def getconn():
        conn = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PUBLIC,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )

    with pool.connect() as db_conn:
        print("Enabling pgvector extension...")
        db_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        db_conn.commit()
        print("pgvector enabled successfully.")
        
    connector.close()

if __name__ == "__main__":
    init_vector_extension()
