from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin_init import db
from routers.auth import get_current_user
import config

router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)

@router.get("/search")
async def search_users(
    query: str,
    user_id: str = Depends(get_current_user)
):
    """
    Search for users by email or display name
    """
    try:
        if not query or len(query) < 3:
            return []
        
        # Search by email (exact match)
        email_query = db.collection(config.USERS_COLLECTION).where(
            "email", "==", query
        )
        
        # Search by display name (starts with)
        display_name_query = db.collection(config.USERS_COLLECTION).where(
            "display_name", ">=", query
        ).where(
            "display_name", "<=", query + "\uf8ff"
        )
        
        # Execute queries
        email_results = list(email_query.stream())
        display_name_results = list(display_name_query.stream())
        
        # Combine results
        all_results = []
        seen_ids = set()
        
        for user in email_results + display_name_results:
            user_id = user.id
            if user_id not in seen_ids:
                user_data = user.to_dict()
                user_data["id"] = user_id
                all_results.append(user_data)
                seen_ids.add(user_id)
        
        return all_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search users: {str(e)}"
        )

@router.get("/{user_id_to_get}")
async def get_user_by_id(
    user_id_to_get: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get user profile by ID
    """
    try:
        user_ref = db.collection(config.USERS_COLLECTION).document(user_id_to_get)
        user = user_ref.get()
        
        if not user.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_data = user.to_dict()
        user_data["id"] = user_id_to_get
        
        return user_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )
