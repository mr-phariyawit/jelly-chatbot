
import logging
import os
from google.cloud import storage
from sqlalchemy.orm import Session
from models import File

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationService:
    def __init__(self, db: Session):
        self.db = db
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "jvc-ai-kms-uploads")
        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise

    def migrate_legacy_files(self):
        """
        Find files where gcs_uri is NULL and content is NOT NULL.
        Upload content to GCS and update gcs_uri.
        """
        files = self.db.query(File).filter(File.gcs_uri.is_(None)).all()
        migrated_count = 0
        skipped_count = 0
        error_count = 0

        logger.info(f"Found {len(files)} legacy files to potentially migrate.")

        for file in files:
            try:
                if not file.content:
                    logger.warning(f"File {file.id} ({file.filename}) has no content and no GCS URI. Skipping.")
                    skipped_count += 1
                    continue

                if file.content.startswith("[Stored in GCS]"):
                     # Should not happen if gcs_uri is None, but sanity check
                     logger.warning(f"File {file.id} has placeholder content but no GCS URI. identifying as skipped.")
                     skipped_count += 1
                     continue
                
                # Logic: Upload file.content (Text) to GCS
                # Note: Legacy content is Text. New uploads might be PDF bytes but legacy is likely extracted text or raw text.
                # We will save it as a text file in GCS.
                
                blob_name = f"{file.bot_id}/{file.id}/{file.filename}.txt" # Append .txt as it is likely raw text
                blob = self.bucket.blob(blob_name)
                
                # Content is string, need to encode
                blob.upload_from_string(file.content, content_type="text/plain")
                
                gcs_uri = f"gs://{self.bucket_name}/{blob_name}"
                
                file.gcs_uri = gcs_uri
                # Optional: Clear content to free space? 
                # Plan says: "Keep it for now" to be safe.
                # file.content = "[Migrated to GCS]" 
                
                self.db.commit()
                migrated_count += 1
                logger.info(f"Migrated file {file.id} to {gcs_uri}")

            except Exception as e:
                logger.error(f"Failed to migrate file {file.id}: {e}")
                error_count += 1
                self.db.rollback()

        return {
            "total_found": len(files),
            "migrated": migrated_count,
            "skipped": skipped_count,
            "errors": error_count
        }
