from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from pydantic import Field
from schemas.user_schemas import UserResponse
from schemas.group_schemas import GroupResponse
from schemas.project_schemas import ProjectCreate, ProjectResponse, ProjectListResponse
from schemas.pyobjectid_schemas import PyObjectId
from models.project_model import Project
from models.user_model import User
from routes.user_routes import get_current_mentor
from beanie import Link
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

async def fetch_mentor(project: Project) -> User:
    """Helper function to fetch mentor safely."""
    try:
        mentor = await project.mentor.fetch() if isinstance(project.mentor, Link) else project.mentor
        if not mentor:
            logger.warning(f"Could not fetch mentor for project {project.id}")
            return None
        return mentor
    except Exception as e:
        logger.warning(f"Error fetching mentor for project {project.id}: {str(e)}")
        return None

async def fetch_groups(project: Project) -> List:
    """Helper function to fetch groups safely."""
    try:
        groups = await project.fetch_link("groups") or []
        return groups
    except Exception as e:
        logger.warning(f"Error fetching groups for project {project.id}: {str(e)}")
        return []

@router.post(
    "/",
    response_model=ProjectResponse,
    description="Create a new project. Only mentors can create projects.",
    summary="Create a new project"
)
async def create_project(project: ProjectCreate, current_user: User = Depends(get_current_mentor)):
    """
    Create a new project with the given details.

    - **title**: The title of the project (required).
    - **description**: A brief description of the project (optional).
    """
    try:
        new_project = Project(
            title=project.title,
            status="Open",
            tags=project.tags,
            description=project.description,
            mentor=Link(current_user, document_class=User),
            groups=[]
        )
        await new_project.insert()
        
        logger.info(f"Created new project: {new_project.id}")
        
        return ProjectResponse(
            _id=str(new_project.id),
            id=str(new_project.id),
            title=new_project.title,
            status=new_project.status,
            tags=new_project.tags,
            description=new_project.description,
            mentor_id=str(current_user.id),
            group_ids=[]
        )
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/",
    response_model=List[ProjectListResponse],
    description="Get a list of all projects with pagination.",
    summary="List all projects"
)
async def get_all_projects(
    skip: int = Query(0, ge=0, description="Number of projects to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of projects to return")
):
    """
    Retrieve a paginated list of all projects.

    - **skip**: Number of projects to skip (default: 0).
    - **limit**: Maximum number of projects to return (default: 50, max: 100).
    """
    try:
        projects = await Project.find_all().skip(skip).limit(limit).to_list()
        result = []

        for project in projects:
            mentor = await fetch_mentor(project)
            groups = await fetch_groups(project)

            result.append(ProjectListResponse(
                _id=str(project.id),
                id=str(project.id),
                title=project.title,
                status=project.status,
                tags=project.tags,
                description=project.description,
                mentor=UserResponse(**mentor.model_dump()) if mentor else None,
                groups=[GroupResponse(**group.model_dump()) for group in groups]
            ))

        return result
    except Exception as e:
        logger.error(f"Error fetching all projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get(
    "/{project_id}",
    response_model=ProjectListResponse,
    description="Get detailed information about a specific project by ID.",
    summary="Get a project by ID"
)
async def get_project_by_id(project_id: str):
    """
    Retrieve a project by its ID.

    - **project_id**: The ID of the project to retrieve.
    """
    try:
        project_id_obj = PyObjectId.validate(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id format")

    try:
        project = await Project.get(project_id_obj)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        mentor = await fetch_mentor(project)
        groups = await fetch_groups(project)

        return ProjectListResponse(
            # _id=str(project.id),
            id=str(project.id),
            title=project.title,
            status=project.status,
            tags=project.tags,
            description=project.description,
            mentor=UserResponse(**mentor.model_dump()) if mentor else None,
            groups=[GroupResponse(**group.model_dump()) for group in groups]
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error fetching project by ID {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put(
    "/{project_id}",
    response_model=dict,
    description="Update an existing project. Only the mentor who created the project can update it.",
    summary="Update a project"
)
async def update_project(project_id: str, project: ProjectCreate, current_user: User = Depends(get_current_mentor)):
    """
    Update a project with the given details.

    - **project_id**: The ID of the project to update.
    - **title**: The updated title of the project (required).
    - **description**: The updated description (optional).
    - **status**: The updated status of the project (optional).
    - **tags**: The updated tags for the project (optional).
    """
    try:
        project_id_obj = PyObjectId.validate(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id format")

    try:
        db_project = await Project.get(project_id_obj)
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Kiểm tra quyền
        mentor = await fetch_mentor(db_project)
        if not mentor or str(mentor.id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        # Cập nhật project
        db_project.title = project.title
        db_project.description = project.description
        db_project.status = "open"
        db_project.tags = project.tags
        await db_project.save()

        groups = await fetch_groups(db_project)

        logger.info(f"Updated project: {db_project.id}")

        return {
            "_id": str(db_project.id),
            "title": db_project.title,
            "description": db_project.description,
            "status": "open",
            "tags": db_project.tags,
            "mentor": UserResponse(**mentor.model_dump()) if mentor else None,
            "groups": [GroupResponse(**group.model_dump()) for group in groups]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete(
    "/{project_id}",
    description="Delete a project and its associated groups and tasks. Only the mentor who created the project can delete it.",
    summary="Delete a project"
)
async def delete_project(project_id: str, current_user: User = Depends(get_current_mentor)):
    """
    Delete a project by its ID, along with all associated groups and tasks.

    - **project_id**: The ID of the project to delete.
    """
    try:
        project_id_obj = PyObjectId.validate(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id format")

    try:
        project = await Project.get(project_id_obj)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        mentor = await fetch_mentor(project)
        if not mentor or str(mentor.id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Not authorized")

        groups = await fetch_groups(project)
        for group in groups:
            tasks = await group.fetch_link("allTasks") or []
            for task in tasks:
                await task.delete()
            await group.delete()

        await project.delete()
        
        logger.info(f"Deleted project: {project_id}")
        
        return {"message": "Project deleted"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")