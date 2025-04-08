from fastapi import APIRouter, Request, Depends, HTTPException, status
from firebase_admin_init import db, is_board_owner, is_board_member
from routers.auth import get_current_user
from google.cloud import firestore
import config
from models import BoardCreate
import uuid

router = APIRouter(
    prefix="/api/boards",
    tags=["boards"]
)

@router.post("/")
async def create_board(
    board_data: BoardCreate,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new task board
    """
    try:
        board_id = str(uuid.uuid4())
        board_ref = db.collection(config.BOARDS_COLLECTION).document(board_id)

        board = {
            "id": board_id,
            "name": board_data.name,
            "description": board_data.description,
            "creator_id": user_id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        }

        board_ref.set(board)

        # Fetch the document again to get resolved timestamps
        created_board = board_ref.get().to_dict()
        return created_board

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create board: {str(e)}"
        )

@router.get("/")
async def get_boards(user_id: str = Depends(get_current_user)):
    try:
        created_boards_query = db.collection(config.BOARDS_COLLECTION).where(
            "creator_id", "==", user_id
        )
        board_users_query = db.collection(config.BOARD_USERS_COLLECTION).where(
            "user_id", "==", user_id
        )

        created_boards = created_boards_query.stream()
        board_users = board_users_query.stream()

        member_board_ids = [bu.to_dict()["board_id"] for bu in board_users]

        member_boards = []
        for board_id in member_board_ids:
            board_ref = db.collection(config.BOARDS_COLLECTION).document(board_id)
            board = board_ref.get()
            if board.exists:
                member_boards.append(board.to_dict())

        all_boards = [board.to_dict() for board in created_boards] + member_boards
        return all_boards

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get boards: {str(e)}"
        )

@router.get("/{board_id}")
async def get_board(board_id: str, user_id: str = Depends(get_current_user)):
    try:
        if not await is_board_member(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this board"
            )

        board_ref = db.collection(config.BOARDS_COLLECTION).document(board_id)
        board = board_ref.get()

        if not board.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found"
            )

        tasks_query = db.collection(config.TASKS_COLLECTION).where(
            "board_id", "==", board_id
        )
        tasks = tasks_query.stream()
        task_list = [task.to_dict() for task in tasks]

        board_users_query = db.collection(config.BOARD_USERS_COLLECTION).where(
            "board_id", "==", board_id
        )
        board_users = board_users_query.stream()
        user_ids = [bu.to_dict()["user_id"] for bu in board_users]

        board_data = board.to_dict()
        creator_id = board_data.get("creator_id")
        if creator_id and creator_id not in user_ids:
            user_ids.append(creator_id)

        users = []
        for uid in user_ids:
            user_ref = db.collection(config.USERS_COLLECTION).document(uid)
            user = user_ref.get()
            if user.exists:
                user_data = user.to_dict()
                user_data["id"] = uid
                users.append(user_data)

        return {
            "board": board_data,
            "tasks": task_list,
            "users": users,
            "is_owner": creator_id == user_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get board: {str(e)}"
        )

@router.put("/{board_id}")
async def update_board(
    board_id: str,
    board_data: BoardCreate,
    user_id: str = Depends(get_current_user)
):
    try:
        if not await is_board_owner(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the board creator can update the board"
            )

        board_ref = db.collection(config.BOARDS_COLLECTION).document(board_id)
        board = board_ref.get()
        if not board.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found"
            )

        update_data = {
            "name": board_data.name,
            "description": board_data.description,
            "updated_at": firestore.SERVER_TIMESTAMP
        }

        board_ref.update(update_data)

        updated_board = board_ref.get().to_dict()
        return updated_board

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update board: {str(e)}"
        )

@router.delete("/{board_id}")
async def delete_board(board_id: str, user_id: str = Depends(get_current_user)):
    try:
        if not await is_board_owner(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the board creator can delete the board"
            )

        tasks_query = db.collection(config.TASKS_COLLECTION).where("board_id", "==", board_id)
        if list(tasks_query.stream()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete board with active tasks. Remove all tasks first."
            )

        board_users_query = db.collection(config.BOARD_USERS_COLLECTION).where("board_id", "==", board_id)
        if list(board_users_query.stream()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete board with other users. Remove all users first."
            )

        board_ref = db.collection(config.BOARDS_COLLECTION).document(board_id)
        board_ref.delete()

        return {"message": "Board deleted successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete board: {str(e)}"
        )

@router.post("/{board_id}/users")
async def add_user_to_board(
    board_id: str,
    user_data: dict,
    user_id: str = Depends(get_current_user)
):
    try:
        if not await is_board_owner(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the board creator can add users"
            )

        email = user_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )

        users_query = db.collection(config.USERS_COLLECTION).where("email", "==", email)
        users = list(users_query.stream())
        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )

        user_to_add = users[0]
        user_to_add_id = user_to_add.id

        if user_to_add_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add yourself to the board"
            )

        board_users_query = db.collection(config.BOARD_USERS_COLLECTION).where(
            "board_id", "==", board_id
        ).where("user_id", "==", user_to_add_id)

        if list(board_users_query.stream()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this board"
            )

        board_user_id = str(uuid.uuid4())
        board_user_ref = db.collection(config.BOARD_USERS_COLLECTION).document(board_user_id)

        board_user_data = {
            "id": board_user_id,
            "board_id": board_id,
            "user_id": user_to_add_id,
            "added_by": user_id,
            "added_at": firestore.SERVER_TIMESTAMP
        }

        board_user_ref.set(board_user_data)

        result = user_to_add.to_dict()
        result["id"] = user_to_add_id
        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add user to board: {str(e)}"
        )

@router.delete("/{board_id}/users/{user_id_to_remove}")
async def remove_user_from_board(
    board_id: str,
    user_id_to_remove: str,
    user_id: str = Depends(get_current_user)
):
    try:
        if not await is_board_owner(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the board creator can remove users"
            )

        board_users_query = db.collection(config.BOARD_USERS_COLLECTION).where(
            "board_id", "==", board_id
        ).where("user_id", "==", user_id_to_remove)

        board_users = list(board_users_query.stream())
        if not board_users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this board"
            )

        for bu in board_users:
            bu.reference.delete()

        tasks_query = db.collection(config.TASKS_COLLECTION).where("board_id", "==", board_id)
        tasks = tasks_query.stream()
        batch = db.batch()

        for task in tasks:
            task_data = task.to_dict()
            assigned_to = task_data.get("assigned_to", [])
            if user_id_to_remove in assigned_to:
                assigned_to.remove(user_id_to_remove)
                unassigned = len(assigned_to) == 0
                batch.update(task.reference, {
                    "assigned_to": assigned_to,
                    "unassigned": unassigned,
                    "updated_at": firestore.SERVER_TIMESTAMP
                })

        batch.commit()

        return {"message": "User removed from board successfully"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove user from board: {str(e)}"
        )
