import json
import os
import uuid
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

from google.cloud import firestore
from google.oauth2 import service_account

# Import your config values
from config import FIREBASE_CONFIG, SERVICE_ACCOUNT_PATH

# Initialize Firestore
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH)
db = firestore.Client(credentials=credentials)


class FirestoreService:
    """Service for interacting with Firestore using google-cloud-firestore SDK (no firebase_admin)"""

    @staticmethod
    def create_document(collection: str, data: Dict[str, Any], document_id: Optional[str] = None) -> Dict[str, Any]:
        if not document_id:
            document_id = str(uuid.uuid4())

        # Firestore server timestamp for datetime fields
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = firestore.SERVER_TIMESTAMP

        db.collection(collection).document(document_id).set(data)
        result = data.copy()
        result['id'] = document_id
        return result

    @staticmethod
    def get_document(collection: str, document_id: str) -> Dict[str, Any]:
        doc = db.collection(collection).document(document_id).get()
        if not doc.exists:
            raise ValueError(f"Document {document_id} not found in {collection}")
        data = doc.to_dict()
        data['id'] = document_id
        return data

    @staticmethod
    def update_document(collection: str, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = firestore.SERVER_TIMESTAMP
        doc_ref = db.collection(collection).document(document_id)
        doc_ref.update(data)
        updated_data = doc_ref.get().to_dict()
        updated_data['id'] = document_id
        return updated_data

    @staticmethod
    def delete_document(collection: str, document_id: str) -> bool:
        db.collection(collection).document(document_id).delete()
        return True

    @staticmethod
    def list_documents(collection: str) -> List[Dict[str, Any]]:
        docs = db.collection(collection).stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]

    @staticmethod
    def query_documents(collection: str, field_path: str, op_string: str, value: Any) -> List[Dict[str, Any]]:
        op_map = {
            "==": "==", ">": ">", ">=": ">=", "<": "<", "<=": "<=", "!=": "!=",
            "EQUAL": "==", "GREATER_THAN": ">", "GREATER_THAN_OR_EQUAL": ">=",
            "LESS_THAN": "<", "LESS_THAN_OR_EQUAL": "<=", "NOT_EQUAL": "!="
        }
        operator = op_map.get(op_string.upper(), "==")
        query = db.collection(collection).where(field_path, operator, value)
        return [{**doc.to_dict(), "id": doc.id} for doc in query.stream()]

    @staticmethod
    def query_documents_array_contains(collection: str, field_path: str, value: Any) -> List[Dict[str, Any]]:
        query = db.collection(collection).where(field_path, "array_contains", value)
        return [{**doc.to_dict(), "id": doc.id} for doc in query.stream()]


class FirebaseAuthService:
    """Service for Firebase Authentication via REST API"""

    FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1"

    @staticmethod
    def sign_up(email: str, password: str) -> Dict[str, Any]:
        url = f"{FirebaseAuthService.FIREBASE_AUTH_URL}/accounts:signUp?key={FIREBASE_CONFIG['apiKey']}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise ValueError(response.json().get("error", {}).get("message", "Sign up failed"))
        return response.json()

    @staticmethod
    def sign_in(email: str, password: str) -> Dict[str, Any]:
        url = f"{FirebaseAuthService.FIREBASE_AUTH_URL}/accounts:signInWithPassword?key={FIREBASE_CONFIG['apiKey']}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise ValueError(response.json().get("error", {}).get("message", "Sign in failed"))
        return response.json()

    @staticmethod
    def verify_id_token(id_token: str) -> Dict[str, Any]:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_CONFIG['apiKey']}"
        payload = {
            "idToken": id_token
        }
        # print("Verifying ID token:", id_token)
        # print("Payload for verification:", payload)
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise ValueError(response.json().get("error", {}).get("message", "Token verification failed"))
        users = response.json().get("users", [])
        print("Users found:", users)
        if not users:
            raise ValueError("No user found for the provided token")
        return users[0] if users else {}

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_CONFIG['apiKey']}"
        payload = {
            "email": [email]
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200 and response.json().get("users"):
            return response.json()["users"][0]
        return None
