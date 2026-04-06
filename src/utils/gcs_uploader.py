"""Utility for uploading raw data snapshots to Google Cloud Storage."""

import json
import logging
from google.cloud import storage

# Configuración de logger para trazabilidad senior
logger = logging.getLogger(__name__)


class GCSUploader:
    """Handles data uploading to GCS buckets."""

    def __init__(self, bucket_name: str, credentials_path: str):
        """Inicializa el cliente de GCS usando la llave JSON local."""
        try:
            self.client = storage.Client.from_service_account_json(
                credentials_path
            )
            self.bucket = self.client.bucket(bucket_name)
        except Exception as e:
            logger.error(f"Error inicializando GCS: {e}")
            raise e

    def upload_data(self, data: dict, destination_blob_name: str):
        """Sube un diccionario como un archivo JSON al bucket de GCP."""
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_string(
                data=json.dumps(data, indent=2, default=str),
                content_type="application/json",
            )
            logger.info(
                f"Successfully uploaded data to gs://{self.bucket.name}/"
                f"{destination_blob_name}"
            )
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            raise e
