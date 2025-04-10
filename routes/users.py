from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from dependencies import get_current_user, get_token_user
from firebase_service import FirebaseAuthService, FirestoreService

router = APIRouter(tags=["users"])

@router.get("/api/users/current")
async def get_current_user_info(
    user_id: str = Depends(get_token_user)
):
    """Get information about the current authenticated user"""
    try:
        # Get user data from firestore
        user = FirestoreService.get_document("users", user_id)
        
        return {
            "user_id": user["id"],
            "email": user.get("email", ""),
            "display_name": user.get("display_name", "User")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users/lookup-email")
async def lookup_user_by_email(
    email: str,
    id_token: str,
    user_id: str = Depends(get_current_user)
):
    """Look up a user by email using Firebase Auth API"""
    try:
        user = FirebaseAuthService.get_user_by_email(email, id_token)
        
        if not user:
            return JSONResponse(
                status_code=404,
                content={"detail": f"User with email {email} not found"}
            )
        
        return {
            "user_id": user.get("localId"),
            "email": user.get("email"),
            "display_name": user.get("displayName", "User")
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
