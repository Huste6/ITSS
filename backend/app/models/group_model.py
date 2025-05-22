from typing import List, Optional
from beanie import Document, Link

class Group(Document):
    name: str
    project: Optional[Link["Project"]]
    leaders: Optional[Link["User"]]
    members: Optional[List[Link["User"]]]
    allTasks: Optional[List[Link["Task"]]]
    github_link: Optional[str] = None  # Thêm trường mới với giá trị mặc định là None
    
    class Settings:
        collection = "groups"
        
from .project_model import Project
from .task_model import Task
from .user_model import User