from fastapi import Request, HTTPException, Depends, Header
from typing import Optional, Union
from firebase_service import FirebaseAuthService

async def get_current_user(request: Request) -> str:
    """Dependency to get current authenticated user from session"""
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="Not logged in")
    return request.session["user_id"]

async def get_current_user_optional(request: Request) -> Optional[str]:
    """Dependency to get current user if logged in, otherwise None"""
    return request.session.get("user_id")

async def get_token_user(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> str:
    """Dependency to get current authenticated user from ID token in Authorization header"""
    # First check session
    if "user_id" in request.session:
        return request.session["user_id"]
    
    # Then check token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify ID token with Firebase
        user_data = FirebaseAuthService.verify_id_token(token)
        
        if not user_data or not user_data.get("uid"):
            raise HTTPException(status_code=401, detail="Invalid ID token")
        
        # Store user ID in session
        user_id = user_data.get("uid")
        request.session["user_id"] = user_id
        
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def get_token_user_optional(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """Dependency to get current user from ID token if authenticated, otherwise None"""
    try:
        return await get_token_user(request, authorization)
    except HTTPException:
        return None
