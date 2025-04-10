import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Firebase configuration for client-side usage
FIREBASE_CONFIG = {
    "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyDOwm_4ohND6EwGYxDObalzZUCfF0-tUsY"),
    "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "task-cdb09.firebaseapp.com"),
    "projectId": os.environ.get("FIREBASE_PROJECT_ID", "task-cdb09"),
    "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "task-cdb09.firebasestorage.app"),
    "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "1078343843242"),
    "appId": os.environ.get("FIREBASE_APP_ID", "1:1078343843242:web:18d3e842759eb38c1abfd3")
}

# Service account file path
SERVICE_ACCOUNT_PATH = "service_account.json"
