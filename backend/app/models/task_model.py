from datetime import datetime
from typing import List, Optional
from beanie import Document, Link



class Task(Document):
    title: str
    description: Optional[str]
    group: Optional[Link["Group"]]
    assigned_students: Optional[List[Link["User"]]]
    status: Optional[str] = None
    deadline: Optional[datetime] = None
    related_to_project: Optional[Link["Project"]] = None
    priority: Optional[str] = None

    
    class Settings:
        collection = "tasks"
        

from .group_model import Group
from .project_model import Project
from .user_model import User