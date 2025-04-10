from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
import requests

from config import FIREBASE_CONFIG
from firebase_service import FirebaseAuthService, FirestoreService

router = APIRouter(tags=["authentication"])
templates = Jinja2Templates(directory="templates")

@router.get("/login")
async def login_page(request: Request):
    if "user_id" in request.session:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "config": {"FIREBASE_CONFIG": FIREBASE_CONFIG}}
    )

@router.get("/register")
async def register_page(request: Request):
    if "user_id" in request.session:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "config": {"FIREBASE_CONFIG": FIREBASE_CONFIG}}
    )

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_CONFIG['apiKey']}"
        headers = {"Content-Type": "application/json"}
        data = {"email": email, "password": password, "returnSecureToken": True}

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        result = response.json()
        id_token = result.get("idToken")
        user_id = result.get("localId")

        if not id_token or not user_id:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # Verify token via backend and set session
        return await create_session_with_token(request, id_token)
    
    except requests.exceptions.HTTPError as e:
        error_message = "Login failed. Please try again."
        try:
            error_data = e.response.json()
            firebase_error = error_data.get("error", {}).get("message", "")
            if firebase_error == "EMAIL_NOT_FOUND":
                error_message = "Email not found. Please register first."
            elif firebase_error == "INVALID_PASSWORD":
                error_message = "Invalid password. Please try again."
            elif firebase_error == "USER_DISABLED":
                error_message = "Account disabled. Please contact support."
        except:
            pass
        raise HTTPException(status_code=401, detail=error_message)

@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(...)
):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_CONFIG['apiKey']}"
        headers = {"Content-Type": "application/json"}
        data = {
            "email": email,
            "password": password,
            "displayName": display_name,
            "returnSecureToken": True
        }

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        result = response.json()
        id_token = result.get("idToken")
        user_id = result.get("localId")

        if not id_token or not user_id:
            raise HTTPException(status_code=400, detail="Failed to register user")

        # Set session via token
        return await create_session_with_token(request, id_token)

    except requests.exceptions.HTTPError as e:
        error_message = "Registration failed. Please try again."
        try:
            error_data = e.response.json()
            firebase_error = error_data.get("error", {}).get("message", "")
            if firebase_error == "EMAIL_EXISTS":
                error_message = "Email already exists. Please use a different email."
            elif firebase_error == "WEAK_PASSWORD":
                error_message = "Password should be at least 6 characters."
        except:
            pass
        raise HTTPException(status_code=400, detail=error_message)

@router.post("/api/auth/session")
async def create_session(request: Request):
    try:
        data = await request.json()
        id_token = data.get("idToken")

        if not id_token:
            print("No ID token received.")
            raise HTTPException(status_code=400, detail="ID token is required")

        print("Received ID token:", id_token, "...")

        user_data = FirebaseAuthService.verify_id_token(id_token)
        if not user_data or not user_data.get("localId"):
            print("Invalid ID token or missing UID.")
            raise HTTPException(status_code=401, detail="Invalid ID token")

        user_id = user_data["localId"]
        request.session["user_id"] = user_id
        print(f"Session established for user: {user_id}")

        # Create user in Firestore if doesn't exist
        try:
            FirestoreService.get_document("users", user_id)
        except Exception as e:
            email = user_data.get("email", "")
            display_name = user_data.get("name") or email.split("@")[0]
            FirestoreService.create_document("users", {
                "email": email,
                "display_name": display_name
            }, document_id=user_id)

        return {"status": "success", "redirect": "/dashboard"}

    except Exception as e:
        print("Session creation error:", str(e))
        raise HTTPException(status_code=401, detail="Authentication failed")

async def create_session_with_token(request: Request, id_token: str):
    try:
        user_data = FirebaseAuthService.verify_id_token(id_token)
        user_id = user_data.get("localId")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid ID token")

        request.session["user_id"] = user_id

        # Ensure user document exists
        try:
            FirestoreService.get_document("users", user_id)
        except:
            email = user_data.get("email", "")
            display_name = user_data.get("name") or email.split("@")[0]
            user_document = {
                "email": email,
                "display_name": display_name
            }
            FirestoreService.create_document("users", user_document, document_id=user_id)

        return {"status": "success", "redirect": "/dashboard"}

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Session creation failed: {str(e)}")

@router.post("/api/auth/logout")
async def api_logout(request: Request):
    request.session.clear()
    return {"status": "success"}

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
