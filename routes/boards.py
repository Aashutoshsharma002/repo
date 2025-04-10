from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import pytz

from dependencies import get_current_user, get_token_user
from firebase_service import FirestoreService, FirebaseAuthService

router = APIRouter(tags=["boards"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
async def dashboard(request: Request, user_id: str = Depends(get_current_user)):
    """Display dashboard with user's boards"""
    # Get boards where user is a member
    boards = FirestoreService.query_documents_array_contains("taskboards", "members", user_id)
    
    # Get user data
    user = FirestoreService.get_document("users", user_id)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "boards": boards,
            "user": user,
            "user_id": user_id
        }
    )

@router.post("/boards/create")
async def create_board(
    request: Request,
    name: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Create a new task board"""
    # Create board in Firestore
    board_data = {
        "name": name,
        "owner_id": user_id,
        "members": [user_id],
        "created_at": datetime.now(pytz.UTC)
    }
    
    new_board = FirestoreService.create_document("taskboards", board_data)
    
    # Redirect to the new board
    return RedirectResponse(url=f"/boards/{new_board['id']}", status_code=303)

@router.get("/boards/{board_id}")
async def get_board(
    request: Request,
    board_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get details of a specific board"""
    # Get board data
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is a member of the board
    if user_id not in board.get("members", []):
        raise HTTPException(status_code=403, detail="You don't have access to this board")
    
    # Get tasks for this board
    tasks = FirestoreService.query_documents("tasks", "board_id", "==", board_id)
    
    # Get all members' data
    members = []
    for member_id in board.get("members", []):
        try:
            member = FirestoreService.get_document("users", member_id)
            members.append(member)
        except:
            # If user doesn't exist, just add the ID
            members.append({"id": member_id, "display_name": "Unknown", "email": ""})
    
    # Count tasks statistics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get("completed", False))
    active_tasks = total_tasks - completed_tasks
    
    return templates.TemplateResponse(
        "board_detail.html",
        {
            "request": request,
            "board": board,
            "tasks": tasks,
            "members": members,
            "user_id": user_id,
            "stats": {
                "total": total_tasks,
                "completed": completed_tasks,
                "active": active_tasks
            }
        }
    )

@router.post("/boards/{board_id}/rename")
async def rename_board(
    board_id: str,
    name: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Rename a board (owner only)"""
    # Get board data
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is the owner
    if user_id != board.get("owner_id"):
        raise HTTPException(status_code=403, detail="Only the owner can rename the board")
    
    # Update board name
    FirestoreService.update_document("taskboards", board_id, {"name": name})
    
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

@router.post("/boards/{board_id}/add-user")
async def add_user_to_board(
    request: Request,
    board_id: str,
    email: str = Form(...),
    user_id: str = Depends(get_current_user),
    id_token: Optional[str] = Form(None)
):
    """Add a user to a board by email (owner only)"""
    # Get board data
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is the owner
    if user_id != board.get("owner_id"):
        raise HTTPException(status_code=403, detail="Only the owner can add users")
    
    # Try to find the user by email
    # This requires having a valid ID token from the client
    if not id_token:
        raise HTTPException(status_code=400, detail="ID token required to lookup users")
    
    try:
        found_user = FirebaseAuthService.get_user_by_email(email, id_token)
        if not found_user:
            raise HTTPException(status_code=404, detail=f"User with email {email} not found")
        
        new_user_id = found_user.get("localId")
        
        # Check if user is already a member
        if new_user_id in board.get("members", []):
            raise HTTPException(status_code=400, detail="User is already a member of this board")
        
        # Add user to members
        members = board.get("members", [])
        members.append(new_user_id)
        
        # Update board
        FirestoreService.update_document("taskboards", board_id, {"members": members})
        
        # Store user in users collection if not exists
        try:
            FirestoreService.get_document("users", new_user_id)
        except:
            user_data = {
                "email": found_user.get("email", ""),
                "display_name": found_user.get("displayName", "User")
            }
            FirestoreService.create_document("users", user_data, document_id=new_user_id)
        
        return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/boards/{board_id}/remove-user")
async def remove_user_from_board(
    board_id: str,
    remove_user_id: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    """Remove a user from a board (owner only)"""
    # Get board data
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is the owner
    if user_id != board.get("owner_id"):
        raise HTTPException(status_code=403, detail="Only the owner can remove users")
    
    # Check if user is trying to remove themselves
    if remove_user_id == user_id:
        raise HTTPException(status_code=400, detail="Owner cannot remove themselves")
    
    # Remove user from members
    members = board.get("members", [])
    if remove_user_id not in members:
        raise HTTPException(status_code=400, detail="User is not a member of this board")
    
    members.remove(remove_user_id)
    
    # Update board
    FirestoreService.update_document("taskboards", board_id, {"members": members})
    
    # Get tasks for the board where this user is assigned
    tasks_for_board = FirestoreService.query_documents("tasks", "board_id", "==", board_id)
    
    # Update each task where the user is assigned
    for task in tasks_for_board:
        assigned_to = task.get("assigned_to", [])
        if remove_user_id in assigned_to:
            # Remove user from assigned_to and set unassigned flag
            assigned_to.remove(remove_user_id)
            
            update_data = {
                "assigned_to": assigned_to,
                "unassigned": len(assigned_to) == 0
            }
            
            FirestoreService.update_document("tasks", task["id"], update_data)
    
    return RedirectResponse(url=f"/boards/{board_id}", status_code=303)

@router.post("/api/boards/create")
async def api_create_board(
    request: Request,
    user_id: str = Depends(get_token_user)
):
    """API endpoint to create a new task board"""
    try:
        # Get request body
        data = await request.json()
        name = data.get("name")
        
        if not name:
            raise HTTPException(status_code=400, detail="Board name is required")
        
        # Create board in Firestore
        board_data = {
            "name": name,
            "owner_id": user_id,
            "members": [user_id],
            "created_at": datetime.now(pytz.UTC)
        }
        
        new_board = FirestoreService.create_document("taskboards", board_data)
        
        # Return the new board
        return {
            "status": "success",
            "board": new_board,
            "redirect": f"/boards/{new_board['id']}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/boards/{board_id}/delete")
async def delete_board(
    board_id: str,
    user_id: str = Depends(get_current_user)
):
    """Delete a board (owner only, if no tasks and no other members)"""
    # Get board data
    try:
        board = FirestoreService.get_document("taskboards", board_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Board not found")
    
    # Check if user is the owner
    if user_id != board.get("owner_id"):
        raise HTTPException(status_code=403, detail="Only the owner can delete the board")
    
    # Check if there are other members
    members = board.get("members", [])
    if len(members) > 1:
        raise HTTPException(status_code=400, detail="Cannot delete board with other members")
    
    # Check if there are tasks
    tasks = FirestoreService.query_documents("tasks", "board_id", "==", board_id)
    
    if len(tasks) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete board with tasks")
    
    # Delete board
    FirestoreService.delete_document("taskboards", board_id)
    
    return RedirectResponse(url="/dashboard", status_code=303)
