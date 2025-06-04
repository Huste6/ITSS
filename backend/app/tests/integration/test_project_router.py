import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from bson import ObjectId
from beanie import Link

# Assuming your main FastAPI app is in main.py
# from main import app
from routes.project_routes import router, fetch_mentor, fetch_groups
from models.project_model import Project
from models.user_model import User
from schemas.project_schemas import ProjectCreate, ProjectResponse, ProjectListResponse
from schemas.user_schemas import UserResponse
from schemas.group_schemas import GroupResponse


# Mock data
MOCK_USER_ID = ObjectId()
MOCK_PROJECT_ID = ObjectId()
MOCK_GROUP_ID = ObjectId()

MOCK_USER_DATA = {
    "id": MOCK_USER_ID,
    "email": "mentor@example.com",
    "username": "mentor_user",
    "role": "mentor"
}

MOCK_PROJECT_DATA = {
    "id": MOCK_PROJECT_ID,
    "title": "Test Project",
    "description": "A test project",
    "status": "Open",
    "tags": ["python", "fastapi"],
    "mentor": None,  # Will be set up in tests
    "groups": []
}

MOCK_GROUP_DATA = {
    "id": MOCK_GROUP_ID,
    "name": "Test Group",
    "description": "A test group"
}


class TestHelperFunctions:
    """Test helper functions used in the route handlers."""
    
    @pytest.mark.asyncio
    async def test_fetch_mentor_success(self):
        """Test successful mentor fetching."""
        mock_user = User(**MOCK_USER_DATA)
        mock_project = MagicMock()
        mock_project.mentor = AsyncMock()
        mock_project.mentor.fetch = AsyncMock(return_value=mock_user)
        mock_project.id = MOCK_PROJECT_ID
        
        # Test with Link
        mock_project.mentor = Link(mock_user, document_class=User)
        with patch.object(Link, 'fetch', return_value=mock_user):
            result = await fetch_mentor(mock_project)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_fetch_mentor_direct_object(self):
        """Test mentor fetching when mentor is direct object."""
        mock_user = User(**MOCK_USER_DATA)
        mock_project = MagicMock()
        mock_project.mentor = mock_user
        mock_project.id = MOCK_PROJECT_ID
        
        result = await fetch_mentor(mock_project)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_fetch_mentor_none(self):
        """Test mentor fetching when mentor is None."""
        mock_project = MagicMock()
        mock_project.mentor = AsyncMock()
        mock_project.mentor.fetch = AsyncMock(return_value=None)
        mock_project.id = MOCK_PROJECT_ID
        
        with patch('isinstance', return_value=True):
            result = await fetch_mentor(mock_project)
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_mentor_exception(self):
        """Test mentor fetching with exception."""
        mock_project = MagicMock()
        mock_project.mentor = AsyncMock()
        mock_project.mentor.fetch = AsyncMock(side_effect=Exception("Database error"))
        mock_project.id = MOCK_PROJECT_ID
        
        with patch('isinstance', return_value=True):
            result = await fetch_mentor(mock_project)
            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_groups_success(self):
        """Test successful groups fetching."""
        mock_groups = [MagicMock(id=MOCK_GROUP_ID)]
        mock_project = MagicMock()
        mock_project.fetch_link = AsyncMock(return_value=mock_groups)
        mock_project.id = MOCK_PROJECT_ID
        
        result = await fetch_groups(mock_project)
        assert result == mock_groups
        mock_project.fetch_link.assert_called_once_with("groups")

    @pytest.mark.asyncio
    async def test_fetch_groups_empty(self):
        """Test groups fetching when no groups exist."""
        mock_project = MagicMock()
        mock_project.fetch_link = AsyncMock(return_value=None)
        mock_project.id = MOCK_PROJECT_ID
        
        result = await fetch_groups(mock_project)
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_groups_exception(self):
        """Test groups fetching with exception."""
        mock_project = MagicMock()
        mock_project.fetch_link = AsyncMock(side_effect=Exception("Database error"))
        mock_project.id = MOCK_PROJECT_ID
        
        result = await fetch_groups(mock_project)
        assert result == []


class TestCreateProject:
    """Test create project endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_project_success(self):
        """Test successful project creation."""
        project_data = {
            "title": "New Project",
            "description": "Project description",
            "tags": ["python"]
        }
        
        mock_user = User(**MOCK_USER_DATA)
        mock_project = MagicMock()
        mock_project.id = MOCK_PROJECT_ID
        mock_project.title = project_data["title"]
        mock_project.description = project_data["description"]
        mock_project.status = "Open"
        mock_project.tags = project_data["tags"]
        
        with patch('routes.project_routes.Project') as MockProject:
            MockProject.return_value = mock_project
            mock_project.insert = AsyncMock()
            
            from routes.project_routes import create_project
            
            result = await create_project(
                ProjectCreate(**project_data),
                current_user=mock_user
            )
            
            assert isinstance(result, ProjectResponse)
            assert result.title == project_data["title"]
            assert result.status == "Open"
            assert str(result.mentor_id) == str(mock_user.id)

    @pytest.mark.asyncio
    async def test_create_project_database_error(self):
        """Test project creation with database error."""
        project_data = {
            "title": "New Project",
            "description": "Project description",
            "tags": ["python"]
        }
        
        mock_user = User(**MOCK_USER_DATA)
        
        with patch('routes.project_routes.Project') as MockProject:
            mock_project = MockProject.return_value
            mock_project.insert = AsyncMock(side_effect=Exception("Database error"))
            
            from routes.project_routes import create_project
            
            with pytest.raises(HTTPException) as exc_info:
                await create_project(
                    ProjectCreate(**project_data),
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "Internal server error"


class TestGetAllProjects:
    """Test get all projects endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_all_projects_success(self):
        """Test successful retrieval of all projects."""
        mock_user = User(**MOCK_USER_DATA)
        mock_group = MagicMock()
        mock_group.model_dump.return_value = MOCK_GROUP_DATA
        
        mock_project = MagicMock()
        mock_project.id = MOCK_PROJECT_ID
        mock_project.title = "Test Project"
        mock_project.status = "Open"
        mock_project.tags = ["python"]
        mock_project.description = "Test description"
        
        mock_find_all = MagicMock()
        mock_find_all.skip.return_value = mock_find_all
        mock_find_all.limit.return_value = mock_find_all
        mock_find_all.to_list = AsyncMock(return_value=[mock_project])
        
        with patch('routes.project_routes.Project.find_all', return_value=mock_find_all), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_user), \
             patch('routes.project_routes.fetch_groups', return_value=[mock_group]):
            
            from routes.project_routes import get_all_projects
            
            result = await get_all_projects(skip=0, limit=50)
            
            assert len(result) == 1
            assert isinstance(result[0], ProjectListResponse)
            assert result[0].title == "Test Project"

    @pytest.mark.asyncio
    async def test_get_all_projects_empty(self):
        """Test retrieval when no projects exist."""
        mock_find_all = MagicMock()
        mock_find_all.skip.return_value = mock_find_all
        mock_find_all.limit.return_value = mock_find_all
        mock_find_all.to_list = AsyncMock(return_value=[])
        
        with patch('routes.project_routes.Project.find_all', return_value=mock_find_all):
            from routes.project_routes import get_all_projects
            
            result = await get_all_projects()
            
            assert result == []

    @pytest.mark.asyncio
    async def test_get_all_projects_database_error(self):
        """Test get all projects with database error."""
        mock_find_all = MagicMock()
        mock_find_all.skip.return_value = mock_find_all
        mock_find_all.limit.return_value = mock_find_all
        mock_find_all.to_list = AsyncMock(side_effect=Exception("Database error"))
        
        with patch('routes.project_routes.Project.find_all', return_value=mock_find_all):
            from routes.project_routes import get_all_projects
            
            with pytest.raises(HTTPException) as exc_info:
                await get_all_projects()
            
            assert exc_info.value.status_code == 500


class TestGetProjectById:
    """Test get project by ID endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_project_by_id_success(self):
        """Test successful retrieval of project by ID."""
        mock_user = User(**MOCK_USER_DATA)
        mock_group = MagicMock()
        mock_group.model_dump.return_value = MOCK_GROUP_DATA
        
        mock_project = MagicMock()
        mock_project.id = MOCK_PROJECT_ID
        mock_project.title = "Test Project"
        mock_project.status = "Open"
        mock_project.tags = ["python"]
        mock_project.description = "Test description"
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=mock_project), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_user), \
             patch('routes.project_routes.fetch_groups', return_value=[mock_group]):
            
            from routes.project_routes import get_project_by_id
            
            result = await get_project_by_id(str(MOCK_PROJECT_ID))
            
            assert isinstance(result, ProjectListResponse)
            assert result.title == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_by_id_invalid_format(self):
        """Test get project by ID with invalid ID format."""
        with patch('routes.project_routes.PyObjectId.validate', side_effect=ValueError("Invalid ID")):
            from routes.project_routes import get_project_by_id
            
            with pytest.raises(HTTPException) as exc_info:
                await get_project_by_id("invalid_id")
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Invalid project_id format"

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self):
        """Test get project by ID when project doesn't exist."""
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=None):
            
            from routes.project_routes import get_project_by_id
            
            with pytest.raises(HTTPException) as exc_info:
                await get_project_by_id(str(MOCK_PROJECT_ID))
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Project not found"


class TestUpdateProject:
    """Test update project endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_project_success(self):
        """Test successful project update."""
        update_data = {
            "title": "Updated Project",
            "description": "Updated description",
            "tags": ["python", "updated"]
        }
        
        mock_user = User(**MOCK_USER_DATA)
        mock_project = MagicMock()
        mock_project.id = MOCK_PROJECT_ID
        mock_project.save = AsyncMock()
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=mock_project), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_user), \
             patch('routes.project_routes.fetch_groups', return_value=[]):
            
            from routes.project_routes import update_project
            
            result = await update_project(
                str(MOCK_PROJECT_ID),
                ProjectCreate(**update_data),
                current_user=mock_user
            )
            
            assert result["title"] == update_data["title"]
            assert result["description"] == update_data["description"]
            assert result["status"] == "open"
            mock_project.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_project_unauthorized(self):
        """Test project update by unauthorized user."""
        update_data = {
            "title": "Updated Project",
            "description": "Updated description",
            "tags": ["python"]
        }
        
        mock_user = User(**MOCK_USER_DATA)
        mock_other_user = User(id=ObjectId(), email="other@example.com", username="other", role="mentor")
        mock_project = MagicMock()
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=mock_project), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_other_user):
            
            from routes.project_routes import update_project
            
            with pytest.raises(HTTPException) as exc_info:
                await update_project(
                    str(MOCK_PROJECT_ID),
                    ProjectCreate(**update_data),
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Not authorized"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self):
        """Test update project when project doesn't exist."""
        update_data = {
            "title": "Updated Project",
            "description": "Updated description",
            "tags": ["python"]
        }
        
        mock_user = User(**MOCK_USER_DATA)
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=None):
            
            from routes.project_routes import update_project
            
            with pytest.raises(HTTPException) as exc_info:
                await update_project(
                    str(MOCK_PROJECT_ID),
                    ProjectCreate(**update_data),
                    current_user=mock_user
                )
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Project not found"


class TestDeleteProject:
    """Test delete project endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_project_success(self):
        """Test successful project deletion."""
        mock_user = User(**MOCK_USER_DATA)
        mock_task = MagicMock()
        mock_task.delete = AsyncMock()
        
        mock_group = MagicMock()
        mock_group.fetch_link = AsyncMock(return_value=[mock_task])
        mock_group.delete = AsyncMock()
        
        mock_project = MagicMock()
        mock_project.id = MOCK_PROJECT_ID
        mock_project.delete = AsyncMock()
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=mock_project), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_user), \
             patch('routes.project_routes.fetch_groups', return_value=[mock_group]):
            
            from routes.project_routes import delete_project
            
            result = await delete_project(str(MOCK_PROJECT_ID), current_user=mock_user)
            
            assert result["message"] == "Project deleted"
            mock_task.delete.assert_called_once()
            mock_group.delete.assert_called_once()
            mock_project.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_project_unauthorized(self):
        """Test project deletion by unauthorized user."""
        mock_user = User(**MOCK_USER_DATA)
        mock_other_user = User(id=ObjectId(), email="other@example.com", username="other", role="mentor")
        mock_project = MagicMock()
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=mock_project), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_other_user):
            
            from routes.project_routes import delete_project
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_project(str(MOCK_PROJECT_ID), current_user=mock_user)
            
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Not authorized"

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self):
        """Test delete project when project doesn't exist."""
        mock_user = User(**MOCK_USER_DATA)
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=None):
            
            from routes.project_routes import delete_project
            
            with pytest.raises(HTTPException) as exc_info:
                await delete_project(str(MOCK_PROJECT_ID), current_user=mock_user)
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Project not found"

    @pytest.mark.asyncio
    async def test_delete_project_no_groups(self):
        """Test project deletion with no associated groups."""
        mock_user = User(**MOCK_USER_DATA)
        mock_project = MagicMock()
        mock_project.id = MOCK_PROJECT_ID
        mock_project.delete = AsyncMock()
        
        with patch('routes.project_routes.PyObjectId.validate', return_value=MOCK_PROJECT_ID), \
             patch('routes.project_routes.Project.get', return_value=mock_project), \
             patch('routes.project_routes.fetch_mentor', return_value=mock_user), \
             patch('routes.project_routes.fetch_groups', return_value=[]):
            
            from routes.project_routes import delete_project
            
            result = await delete_project(str(MOCK_PROJECT_ID), current_user=mock_user)
            
            assert result["message"] == "Project deleted"
            mock_project.delete.assert_called_once()


# Integration test setup (if you want to test with TestClient)
class TestProjectRoutesIntegration:
    """Integration tests using TestClient."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        # You'll need to import your main FastAPI app here
        # from main import app
        # return TestClient(app)
        pass
    
    def test_create_project_integration(self, client):
        """Integration test for project creation."""
        # This would test the actual HTTP endpoints
        pass


if __name__ == "__main__":
    pytest.main([__file__])