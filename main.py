import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import json
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from database import db
from routers import auth, boards, tasks, users

# Helper function to get Firebase configuration
def get_firebase_config():
    """Helper function to get consistent Firebase configuration"""
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "task-cdb09")
    return {
        "apiKey": os.environ.get("FIREBASE_API_KEY", "AIzaSyDOwm_4ohND6EwGYxDObalzZUCfF0-tUsY"),
        "projectId": project_id,
        "appId": os.environ.get("FIREBASE_APP_ID", "1:1078343843242:web:18d3e842759eb38c1abfd3"),
        "authDomain": f"{project_id}.firebaseapp.com",
        "storageBucket": f"{project_id}.firebasestorage.app",
        "messagingSenderId": "1078343843242"
    }

app = FastAPI(title="Task Management System")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Authentication dependency 
async def get_current_user(request: Request):
    """
    Authentication dependency - verifies Firebase ID token using the router's function
    """
    return await auth.get_current_user(request)

# Create a public router and a protected router
# Public router doesn't require authentication
public_router = auth.router

# Protected routes require authentication
boards_router = boards.router
tasks_router = tasks.router
users_router = users.router

# Include routers with appropriate dependencies
app.include_router(public_router)
app.include_router(boards_router, dependencies=[Depends(get_current_user)])
app.include_router(tasks_router, dependencies=[Depends(get_current_user)])
app.include_router(users_router, dependencies=[Depends(get_current_user)])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Serve the main index page. Authentication is handled client-side by Firebase.
    """
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "firebase_config": get_firebase_config()
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Serve the login page with Firebase configuration.
    """
    return templates.TemplateResponse(
        "login.html", 
        {
            "request": request,
            "firebase_config": get_firebase_config()
        }
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Serve the registration page with Firebase configuration.
    """
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request,
            "firebase_config": get_firebase_config()
        }
    )

@app.get("/board/{board_id}", response_class=HTMLResponse)
async def board_page(request: Request, board_id: str):
    """
    Serve the board detail page. Authentication is handled client-side by Firebase.
    """
    return templates.TemplateResponse(
        "board.html", 
        {
            "request": request, 
            "board_id": board_id,
            "firebase_config": get_firebase_config()
        }
    )

# Directly serve the app with Uvicorn if run directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
