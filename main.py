import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from routes import auth, boards, tasks, users

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Task Board Management System")

# Add session middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get("SESSION_SECRET", "supersecretkey"),
    max_age=3600  # 1 hour session
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router)
app.include_router(boards.router)
app.include_router(tasks.router)
app.include_router(users.router)

@app.get("/")
async def root(request: Request):
    # If user is logged in, redirect to dashboard
    if "user_id" in request.session:
        return RedirectResponse(url="/dashboard")
    # Otherwise redirect to login page
    return RedirectResponse(url="/login")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
