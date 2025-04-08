"""
Helper functions for the Task Management System
"""
import config
from database import db

# Helper function to check board ownership
async def is_board_owner(board_id: str, user_id: str) -> bool:
    """
    Check if the user is the owner of the board
    """
    board_ref = db.collection(config.BOARDS_COLLECTION).document(board_id)
    board = board_ref.get()
    
    if not board.exists:
        return False
    
    board_data = board.to_dict()
    return board_data.get("creator_id") == user_id

# Helper function to check board membership
async def is_board_member(board_id: str, user_id: str) -> bool:
    """
    Check if the user is a member of the board
    """
    # Check if user is the creator first
    if await is_board_owner(board_id, user_id):
        return True
        
    # Check if user is a member
    board_user_ref = db.collection(config.BOARD_USERS_COLLECTION).where(
        "board_id", "==", board_id).where("user_id", "==", user_id)
    
    users = board_user_ref.stream()
    return len(list(users)) > 0