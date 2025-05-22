from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from bson import ObjectId
from pydantic_core import core_schema
from schemas.pyobjectid_schemas import PyObjectId



class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    group_id: PyObjectId
    assigned_student_ids: List[str]
    status: Optional[str] = "todo"
    deadline: Optional[datetime] = None
    priority: Optional[str] = None

class TaskResponse(BaseModel):
    _id: PyObjectId
    id : str
    title: str
    description: Optional[str]
    group_id: str
    group_name: str
    assigned_students: List[Dict[str, str]] 
    status: Optional[str] = "todo"
    deadline: Optional[datetime] = None
    priority: Optional[str] = None
    

    class Config:
        from_attributes = True