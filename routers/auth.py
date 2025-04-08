from fastapi import APIRouter, Request, HTTPException, status
from google.cloud import firestore
import requests
import os
from dotenv import load_dotenv
from database import db
import config
from fastapi import Depends


load_dotenv()

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"]
)

async def verify_firebase_token(token: str) -> dict:
    """
    Verify a Firebase ID token using the Firebase Auth REST API
    """
    try:
        api_key = os.environ.get("FIREBASE_API_KEY", "")
        if not api_key:
            raise ValueError("Firebase API key not found in environment variables")

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
        response = requests.post(url, json={"idToken": token})
        data = response.json()

        if "error" in data:
            raise ValueError(f"Token verification failed: {data['error']['message']}")

        return data["users"][0]
    except Exception as e:
        raise ValueError(f"Token verification failed: {str(e)}")

@router.post("/save-user-data")
async def save_user_data(request: Request):
    """
    Save user data to Firestore after client-side auth
    This endpoint should be public, called immediately after login
    """
    try:
        data = await request.json()
        id_token = data.get("idToken")

        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token is required"
            )

        user_data = await verify_firebase_token(id_token)
        uid = user_data["localId"]
        email = user_data.get("email", "")
        display_name = user_data.get("displayName") or email.split('@')[0]

        user_ref = db.collection(config.USERS_COLLECTION).document(uid)
        user_ref.set({
            "id": uid,
            "email": email,
            "display_name": display_name,
            "last_login": firestore.SERVER_TIMESTAMP,
            "created_at": firestore.SERVER_TIMESTAMP
        }, merge=True)

        return {"success": True, "user_id": uid}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to save user data: {str(e)}"
        )

@router.get("/user")
async def get_user(request: Request):
    """
    Get current user info if authenticated. Returns anonymous info if not.
    """
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
        try:
            user_data = await verify_firebase_token(token)
            user_id = user_data["localId"]

            user_doc = db.collection(config.USERS_COLLECTION).document(user_id).get()
            if user_doc.exists:
                return {
                    "user": user_doc.to_dict(),
                    "authenticated": True
                }
        except Exception:
            pass  # Silent fail, return anonymous info

    return {
        "user": None,
        "authenticated": False
    }


async def get_current_user(request: Request) -> str:
    """
    Extract and verify Firebase token from Authorization header.
    Returns the UID of the authenticated user.
    """
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing or invalid"
        )

    token = authorization.replace("Bearer ", "")
    try:
        user_data = await verify_firebase_token(token)
        return user_data["localId"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )