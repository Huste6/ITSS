from typing import Optional, List, Any
from pydantic import BaseModel, Field
from schemas.pyobjectid_schemas import PyObjectId
from bson import ObjectId
from schemas.user_schemas import UserResponse
from schemas.group_schemas import GroupResponse

class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    _id: PyObjectId
    id : str
    title: str
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    mentor: Optional[UserResponse] = None
    groups: Optional[List[str]] = None
    status: Optional[str] = "Open" #default status
    class Config:
        from_attributes = True

class ProjectListResponse(BaseModel):
    _id: PyObjectId
    id : str
    title: str
    tags: Optional[List[str]] = None
    description: Optional[str] = None
    mentor: Optional["UserResponse"] = None
    groups: Optional[List["GroupResponse"]] = None
    status: Optional[str] = "Open" #default status
    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {ObjectId: str}