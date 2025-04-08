from fastapi import APIRouter, Depends, HTTPException, status
from firebase_admin_init import db, is_board_member
from routers.auth import get_current_user
from google.cloud import firestore
import config
from models import TaskCreate, Task
from typing import List
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"]
)

@router.post("/")
async def create_task(
    task_data: TaskCreate, 
    board_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new task in a board - user must be a member of the board
    """
    try:
        # Check if user is a member of the board
        if not await is_board_member(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add tasks to this board"
            )
        
        # Check if a task with the same title already exists in this board
        task_query = db.collection(config.TASKS_COLLECTION).where(
            "board_id", "==", board_id
        ).where(
            "title", "==", task_data.title
        )
        
        existing_tasks = list(task_query.stream())
        if existing_tasks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A task with this title already exists in this board"
            )
        
        # Generate a task ID
        task_id = str(uuid.uuid4())
        
        # Prepare task data
        task = {
            "id": task_id,
            "board_id": board_id,
            "title": task_data.title,
            "description": task_data.description,
            "due_date": task_data.due_date,
            "assigned_to": task_data.assigned_to or [],
            "creator_id": user_id,
            "completed": False,
            "completed_at": None,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "unassigned": len(task_data.assigned_to or []) == 0
        }
        
        # Create task in Firestore
        task_ref = db.collection(config.TASKS_COLLECTION).document(task_id)
        task_ref.set(task)
        
        # Get the created task
        created_task = task_ref.get().to_dict()
        return created_task
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )

@router.get("/{task_id}")
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get a specific task by ID - user must be a member of the board
    """
    try:
        # Get task
        task_ref = db.collection(config.TASKS_COLLECTION).document(task_id)
        task = task_ref.get()
        
        if not task.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task_data = task.to_dict()
        board_id = task_data.get("board_id")
        
        # Check if user is a member of the board
        if not await is_board_member(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this task"
            )
        
        return task_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task: {str(e)}"
        )

@router.put("/{task_id}")
async def update_task(
    task_id: str,
    task_data: TaskCreate,
    user_id: str = Depends(get_current_user)
):
    """
    Update a task - user must be a member of the board
    """
    try:
        # Get task
        task_ref = db.collection(config.TASKS_COLLECTION).document(task_id)
        task = task_ref.get()
        
        if not task.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task_dict = task.to_dict()
        board_id = task_dict.get("board_id")
        
        # Check if user is a member of the board
        if not await is_board_member(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task"
            )
        
        # Check if there's another task with the same title
        if task_data.title != task_dict.get("title"):
            task_query = db.collection(config.TASKS_COLLECTION).where(
                "board_id", "==", board_id
            ).where(
                "title", "==", task_data.title
            )
            
            existing_tasks = list(task_query.stream())
            if existing_tasks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A task with this title already exists in this board"
                )
        
        # Prepare update data
        update_data = {
            "title": task_data.title,
            "description": task_data.description,
            "due_date": task_data.due_date,
            "assigned_to": task_data.assigned_to or [],
            "updated_at": firestore.SERVER_TIMESTAMP,
            "unassigned": len(task_data.assigned_to or []) == 0
        }
        
        # Update task
        task_ref.update(update_data)
        
        # Get updated task
        updated_task = task_ref.get().to_dict()
        return updated_task
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )

@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a task - user must be a member of the board
    """
    try:
        # Get task
        task_ref = db.collection(config.TASKS_COLLECTION).document(task_id)
        task = task_ref.get()
        
        if not task.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task_dict = task.to_dict()
        board_id = task_dict.get("board_id")
        
        # Check if user is a member of the board
        if not await is_board_member(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this task"
            )
        
        # Delete task
        task_ref.delete()
        
        return {"message": "Task deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )

@router.put("/{task_id}/complete")
async def toggle_task_completion(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Toggle task completion status - user must be a member of the board
    """
    try:
        # Get task
        task_ref = db.collection(config.TASKS_COLLECTION).document(task_id)
        task = task_ref.get()
        
        if not task.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task_dict = task.to_dict()
        board_id = task_dict.get("board_id")
        
        # Check if user is a member of the board
        if not await is_board_member(board_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this task"
            )
        
        # Toggle completion
        current_status = task_dict.get("completed", False)
        new_status = not current_status
        
        update_data = {
            "completed": new_status,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        
        # If task is being marked complete, add completion timestamp
        if new_status:
            update_data["completed_at"] = firestore.SERVER_TIMESTAMP
        else:
            update_data["completed_at"] = None
        
        # Update task
        task_ref.update(update_data)
        
        # Get updated task
        updated_task = task_ref.get().to_dict()
        return updated_task
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task completion: {str(e)}"
        )
