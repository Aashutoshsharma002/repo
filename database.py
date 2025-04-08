"""
Database initialization module
"""
from google.cloud import firestore
import config

# Initialize Firestore client
db = firestore.Client.from_service_account_json(config.SERVICE_ACCOUNT_PATH)