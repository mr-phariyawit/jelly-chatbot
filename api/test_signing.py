from datetime import timedelta
from google.cloud import storage
import google.auth

def generate_signed_url_test():
    bucket_name = "ai-kms-platform-uploads"
    blob_name = "test/signed_url_check.txt"
    service_account_email = "687023036300-compute@developer.gserviceaccount.com"
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    print(f"Generating URL for {bucket_name}/{blob_name}")
    print(f"Using SA: {service_account_email}")

    credentials, project_id = google.auth.default()
    if hasattr(credentials, "service_account_email"):
        print(f"Creds Email: {credentials.service_account_email}")

    try:
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type="text/plain",
            service_account_email=service_account_email,
            access_token=None
        )
        print(f"Success: {url}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_signed_url_test()
