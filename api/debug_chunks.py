import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import File, FileChunk

# Setup DB connection
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def inspect_file_chunks(filename_pattern):
    print(f"Searching for file matching: {filename_pattern}")
    file = db.query(File).filter(File.filename.ilike(f"%{filename_pattern}%")).first()
    
    if not file:
        print("File not found!")
        return

    print(f"File ID: {file.id}")
    print(f"Filename: {file.filename}")
    print(f"Status: {file.status}")
    print(f"Content (Preview): {file.content[:100] if file.content else 'None'}")
    
    chunks = db.query(FileChunk).filter(FileChunk.file_id == file.id).all()
    print(f"Total Chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\n--- Chunk {i} (Index {chunk.chunk_index}) ---")
        print(chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content)

if __name__ == "__main__":
    inspect_file_chunks("Baramee")
