from typing import List, Optional
from pydantic import Field
from beanie import Document, Link

class Project(Document):
    title: str
    description: Optional[str]
    mentor: Optional[Link["User"]]
    groups: Optional[List[Link["Group"]]]
    status: Optional[str] = "Open" #default status
    tags: Optional[List[str]] = []  # List of tags


    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Project Title",
                "description": "Project Description",
                "mentor": "Mentor ID",
                "groups": ["Group ID 1", "Group ID 2"],
                "status": "In Progress",
                "progress": 30.0,
                "tags": ["AI", "ML", "backend"]
            }
        }

    class Settings:
        collection = "projects"
        
from .group_model import Group
from .user_model import User