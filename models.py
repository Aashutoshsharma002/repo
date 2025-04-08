from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# User Model
class User(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# Board Model
class BoardCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Board(BoardCreate):
    id: str
    creator_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

# Task Model
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[List[str]] = Field(default_factory=list)

class Task(TaskCreate):
    id: str
    board_id: str
    creator_id: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    unassigned: bool = False

# Board User Model
class BoardUserCreate(BaseModel):
    user_id: str
    board_id: str

class BoardUser(BoardUserCreate):
    id: str
    added_by: str
    added_at: datetime = Field(default_factory=datetime.now)
