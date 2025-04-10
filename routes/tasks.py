from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from datetime import datetime
import pytz

from dependencies import get_current_user, get_token_user
from firebase_service import FirestoreService

router = APIRouter(tags=["tasks"])
templates = Jinja2Templates(directory="templates")

@router.post("/tasks/create")
async def create_task(
    request: Request,
    board_id: str = Form(...),
    title: str = Form(...),
    due_date: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Create a new task in a board"""
    # Get board data to check if user is a member
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is a member of the board
    if user_id not in board.get("members", []):
        raise HTTPException(status_code=403, detail="You don't have access to this board")
    
    # Parse due date
    try:
        due_date_obj = datetime.fromisoformat(due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid due date format")
    
    # Create task in Firestore
    task_data = {
        "title": title,
        "due_date": due_date_obj,
        "completed": False,
        "completed_at": None,
        "board_id": board_id,
        "assigned_to": [],  # Initially no assignments
        "unassigned": True,
        "created_at": datetime.now(pytz.UTC),
        "created_by": user_id
    }
    
    FirestoreService.create_document("tasks", task_data)
    
    # Redirect to the board
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

@router.post("/tasks/{task_id}/edit")
async def edit_task(
    task_id: str,
    title: str = Form(...),
    due_date: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Edit a task"""
    # Get task data
    try:
        task = FirestoreService.get_document("tasks", task_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get board to check permissions
    board_id = task.get("board_id")
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is a member of the board
    if user_id not in board.get("members", []):
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Parse due date
    try:
        due_date_obj = datetime.fromisoformat(due_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid due date format")
    
    # Update task
    update_data = {
        "title": title,
        "due_date": due_date_obj
    }
    
    FirestoreService.update_document("tasks", task_id, update_data)
    
    # Redirect to the board
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

@router.post("/tasks/{task_id}/delete")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a task"""
    # Get task data
    try:
        task = FirestoreService.get_document("tasks", task_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get board to check permissions
    board_id = task.get("board_id")
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is a member of the board
    if user_id not in board.get("members", []):
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Delete task
    FirestoreService.delete_document("tasks", task_id)
    
    # Redirect to the board
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

@router.post("/tasks/{task_id}/toggle-complete")
async def toggle_task_complete(
    task_id: str,
    user_id: str = Depends(get_current_user)
):
    """Toggle task completion status"""
    # Get task data
    try:
        task = FirestoreService.get_document("tasks", task_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get board to check permissions
    board_id = task.get("board_id")
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is a member of the board
    if user_id not in board.get("members", []):
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Toggle completed status
    completed = not task.get("completed", False)
    
    update_data = {
        "completed": completed,
        "completed_at": datetime.now(pytz.UTC) if completed else None
    }
    
    FirestoreService.update_document("tasks", task_id, update_data)
    
    # Redirect to the board
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

@router.post("/api/tasks/create")
async def api_create_task(
    request: Request,
    user_id: str = Depends(get_token_user)
):
    """API endpoint to create a new task"""
    try:
        # Get request body
        data = await request.json()
        
        # Validate required fields
        board_id = data.get("board_id")
        title = data.get("title")
        due_date = data.get("due_date")
        
        if not board_id:
            raise HTTPException(status_code=400, detail="Board ID is required")
        if not title:
            raise HTTPException(status_code=400, detail="Task title is required")
        if not due_date:
            raise HTTPException(status_code=400, detail="Due date is required")
        
        # Get board data to check if user is a member
        try:
            board = FirestoreService.get_document("taskboards", board_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Board not found")
        
        # Check if user is a member of the board
        if user_id not in board.get("members", []):
            raise HTTPException(status_code=403, detail="You don't have access to this board")
        
        # Parse due date
        try:
            due_date_obj = datetime.fromisoformat(due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid due date format")
        
        # Create task in Firestore
        task_data = {
            "title": title,
            "due_date": due_date_obj,
            "completed": False,
            "completed_at": None,
            "board_id": board_id,
            "assigned_to": data.get("assigned_to", []),
            "unassigned": not bool(data.get("assigned_to")),
            "created_at": datetime.now(pytz.UTC),
            "created_by": user_id
        }
        
        new_task = FirestoreService.create_document("tasks", task_data)
        
        return {
            "status": "success",
            "task": new_task,
            "redirect": f"/boards/{board_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/tasks/{task_id}/toggle-complete")
async def api_toggle_task_complete(
    task_id: str,
    user_id: str = Depends(get_token_user)
):
    """API endpoint to toggle task completion status"""
    try:
        # Get task data
        try:
            task = FirestoreService.get_document("tasks", task_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get board to check permissions
        board_id = task.get("board_id")
        try:
            board = FirestoreService.get_document("taskboards", board_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Board not found")
        
        # Check if user is a member of the board
        if user_id not in board.get("members", []):
            raise HTTPException(status_code=403, detail="You don't have access to this task")
        
        # Toggle completed status
        completed = not task.get("completed", False)
        
        update_data = {
            "completed": completed,
            "completed_at": datetime.now(pytz.UTC) if completed else None
        }
        
        updated_task = FirestoreService.update_document("tasks", task_id, update_data)
        
        return {
            "status": "success",
            "task": updated_task,
            "completed": completed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tasks/{task_id}/assign")
async def assign_task(
    task_id: str,
    assigned_to: List[str] = Form([]),
    user_id: str = Depends(get_current_user)
):
    """Assign users to a task"""
    # Get task data
    try:
        task = FirestoreService.get_document("tasks", task_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get board to check permissions
    board_id = task.get("board_id")
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is a member of the board
    if user_id not in board.get("members", []):
        raise HTTPException(status_code=403, detail="You don't have access to this task")
    
    # Ensure all assigned users are members of the board
    for user in assigned_to:
        if user not in board.get("members", []):
            raise HTTPException(status_code=400, detail=f"User {user} is not a member of this board")
    
    # Update task
    unassigned = len(assigned_to) == 0
    update_data = {
        "assigned_to": assigned_to,
        "unassigned": unassigned
    }
    
    FirestoreService.update_document("tasks", task_id, update_data)
    
    # Redirect to the board
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
