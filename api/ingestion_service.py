
import logging
from typing import List
from sqlalchemy.orm import Session
from models import File, FileChunk
import google.generativeai as genai
from google.cloud import storage
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE = 1000
EMBEDDING_MODEL = 'models/text-embedding-004'

class IngestionService:
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
        else:
            logger.warning("GEMINI_API_KEY not set for IngestionService")

    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
        """Split text into chunks of approximately chunk_size characters."""
        # Simple splitting by double newline to preserve paragraphs, then length
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
                
                # Handle single huge paragraphs
                if len(current_chunk) > chunk_size:
                    # Hard split
                    while len(current_chunk) > chunk_size:
                        chunks.append(current_chunk[:chunk_size])
                        current_chunk = current_chunk[chunk_size:]
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def _parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        import io
        from pypdf import PdfReader
        
        try:
            reader = PdfReader(io.BytesIO(content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise

    def _parse_csv(self, content: bytes) -> str:
        """Convert CSV to descriptive text."""
        import io
        import pandas as pd
        
        try:
            df = pd.read_csv(io.BytesIO(content))
            text_lines = []
            for _, row in df.iterrows():
                # Convert row to "Key: Value; Key: Value" format
                row_str = "; ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                text_lines.append(row_str)
            return "\n\n".join(text_lines)
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise

    def _parse_excel(self, content: bytes) -> str:
        """Convert Excel to descriptive text."""
        import io
        import pandas as pd
        
        try:
            df = pd.read_excel(io.BytesIO(content))
            text_lines = []
            for _, row in df.iterrows():
                row_str = "; ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                text_lines.append(row_str)
            return "\n\n".join(text_lines)
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise

    def download_from_gcs(self, gcs_uri: str) -> bytes:
        """Download file bytes from GCS URI (gs://bucket/blob)."""
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")
        
        try:
            # Parse gs://bucket/blob_name
            parts = gcs_uri[5:].split("/", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid GCS URI format: {gcs_uri}")
                
            bucket_name, blob_name = parts
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"GCS Download Error: {e}")
            raise

    def process_file(self, db: Session, file_id: str, content_override: str = None):
        """Read file content (or use override), chunk it, embed it, and save chunks."""
        file = db.query(File).filter(File.id == file_id).first()
        if not file:
            logger.warning(f"File {file_id} not found")
            return
        
        # Determine content
        raw_text = content_override if content_override else file.content
        
        # GCS Support: If no content but we have a GCS URI, download it
        if not raw_text and file.gcs_uri:
            logger.info(f"Downloading file {file.filename} from GCS: {file.gcs_uri}")
            try:
                content_bytes = self.download_from_gcs(file.gcs_uri)
                # Use the helper extraction method (we need to be sure we are adding it below)
                # Ensure we have the helper or add it now.
                # Assuming extract_text is added to class.
                raw_text = self.extract_text(content_bytes, file.content_type)
            except Exception as e:
                logger.error(f"Failed to download/parse from GCS: {e}")
                # Update status to failed? The caller `process_file_background` handles exceptions but let's raise
                raise e

        
        # If content is empty/None, it might be binary (though currently File model stores string 'content')
        # Wait, the File model creates a 'content' Text column.
        # If I upload a PDF, main.py tries to decode utf-8. If that fails, it might fail upload or store garbage.
        # I need to verify main.py upload handling for binary files.
        # Assuming main.py was updated to handle binary uploads (it wasn't fully checked yet).
        # Let's assume for now main.py might need modification to store binary or we re-read from temp?
        # No, the models.py has `content = Column(Text)`. It cannot store binary PDF.
        # CRITICAL: `File` model needs to store binary OR we process immediately before saving.
        # Given the current File model, we are stuck with Text.
        # UPDATE: `process_file` is called AFTER upload.
        # So we must modify `main.py` to NOT try decoding PDF as utf-8, but maybe store Base64?
        # OR better: Parse PDF *in main.py* before saving to `File.content`.
        # YES. That is cleaner for the current Schema.
        # `IngestionService` can expose `extract_text(file: UploadFile)` helper.
        
        pass 
        # I will refactor IngestionService to provide extraction methods, 
        # BUT `process_file` expects the text to be in `File.content` already for RAG.
        # So, step back:
        # 1. Update `ingestion_service` to include `extract_text_from_file`.
        # 2. Update `main.py` to call `extract_text_from_file` BEFORE saving `File`.
        # 3. `process_file` then just takes the text and chunks it.
        
        # Retaining original logic for process_file but adding extraction helper below.
        
        if not raw_text:
             logger.warning(f"File {file.filename} has no content")
             return

        # 1. Chunking
        text_chunks = self.chunk_text(raw_text)
        logger.info(f"Split file {file.filename} into {len(text_chunks)} chunks")

        # 2. Embedding & Saving
        try:
            # Delete existing chunks
            db.query(FileChunk).filter(FileChunk.file_id == file_id).delete()
            
            for index, chunk_text in enumerate(text_chunks):
                if not chunk_text.strip():
                    continue

                # Generate Embedding
                embedding_result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=chunk_text,
                    task_type="retrieval_document"
                )
                embedding_vector = embedding_result['embedding']

                # Create Chunk Record
                import uuid
                new_chunk = FileChunk(
                    id=str(uuid.uuid4()),
                    file_id=file_id,
                    chunk_index=index,
                    content=chunk_text,
                    embedding=embedding_vector
                )
                db.add(new_chunk)
            
            db.commit()
            logger.info(f"Successfully ingested file {file.filename}")

        except Exception as e:
            logger.error(f"Failed to ingest file {file.filename}: {e}")
            db.rollback()
            raise e

    def extract_text(self, content: bytes, content_type: str) -> str:
        """Extract text from raw bytes based on Content-Type"""
        if content_type == "application/pdf":
            return self._parse_pdf(content)
        elif content_type in ["text/csv", "application/vnd.ms-excel"]:
            return self._parse_csv(content)
        elif content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return self._parse_excel(content)
        else:
            # Default to text
            return content.decode('utf-8', errors='ignore')
