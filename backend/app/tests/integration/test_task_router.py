import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId
from beanie import Link

# Import your main app and models
from main import app  # Adjust import path as needed
from models.task_model import Task
from models.group_model import Group
from models.user_model import User
from models.project_model import Project
from schemas.pyobjectid_schemas import PyObjectId

client = TestClient(app)

# Mock data
mock_user_id = ObjectId()
mock_group_id = ObjectId()
mock_task_id = ObjectId()
mock_project_id = ObjectId()
mock_student_id = ObjectId()

mock_user = User(
    id=mock_user_id,
    ho_ten="Test Mentor",
    email="mentor@test.com",
    role="mentor"
)

mock_student = User(
    id=mock_student_id,
    ho_ten="Test Student",
    email="student@test.com",
    role="student"
)

mock_project = Project(
    id=mock_project_id,
    name="Test Project"
)

mock_group = Group(
    id=mock_group_id,
    name="Test Group",
    project=Link(mock_project, document_class=Project),
    allTasks=[]
)

mock_task = Task(
    id=mock_task_id,
    title="Test Task",
    description="Test Description",
    group=Link(mock_group, document_class=Group),
    assigned_students=[Link(mock_student, document_class=User)],
    status="pending",
    deadline=datetime.now(timezone.utc),
    related_to_project=Link(mock_project, document_class=Project),
    priority="Medium",
    created_at=datetime.now(timezone.utc)
)

@pytest.fixture
def mock_current_user():
    with patch("routes.task_routes.get_current_user", return_value=mock_user):
        yield mock_user

class TestCreateTask:
    @patch("models.task_model.Task.save")
    @patch("models.group_model.Group.save") 
    @patch("models.group_model.Group.get")
    @patch("models.user_model.User.get")
    async def test_create_task_success(self, mock_user_get, mock_group_get, mock_group_save, mock_task_save, mock_current_user):
        # Setup mocks
        mock_group_get.return_value = mock_group
        mock_group.project.fetch = AsyncMock(return_value=mock_project)
        mock_user_get.return_value = mock_student
        mock_group.fetch_link = AsyncMock(return_value=[])
        mock_task_save.return_value = None
        mock_group_save.return_value = None
        
        task_data = {
            "title": "New Task",
            "description": "New Task Description",
            "group_id": str(mock_group_id),
            "assigned_student_ids": [str(mock_student_id)],
            "status": "pending",
            "deadline": "2024-12-31T23:59:59Z",
            "priority": "High"
        }
        
        with patch("models.task_model.Task.__init__", return_value=None):
            with patch("models.task_model.Task.id", mock_task_id):
                with patch("models.task_model.Task.title", task_data["title"]):
                    with patch("models.task_model.Task.description", task_data["description"]):
                        with patch("models.task_model.Task.status", task_data["status"]):
                            with patch("models.task_model.Task.priority", task_data["priority"]):
                                with patch("models.task_model.Task.deadline", datetime.fromisoformat(task_data["deadline"].replace('Z', '+00:00'))):
                                    with patch("models.task_model.Task.assigned_students", [Link(mock_student, document_class=User)]):
                                        response = client.post("/tasks/", json=task_data)
        
        assert response.status_code == 200
        assert "title" in response.json()

    @patch("models.group_model.Group.get")
    def test_create_task_group_not_found(self, mock_group_get, mock_current_user):
        mock_group_get.return_value = None
        
        task_data = {
            "title": "New Task",
            "description": "New Task Description", 
            "group_id": str(mock_group_id),
            "assigned_student_ids": [str(mock_student_id)],
            "status": "pending",
            "deadline": "2024-12-31T23:59:59Z"
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 404
        assert "Group not found" in response.json()["detail"]

    @patch("models.group_model.Group.get")
    @patch("models.user_model.User.get")
    async def test_create_task_student_not_found(self, mock_user_get, mock_group_get, mock_current_user):
        mock_group_get.return_value = mock_group
        mock_group.project.fetch = AsyncMock(return_value=mock_project)
        mock_user_get.return_value = None
        
        task_data = {
            "title": "New Task",
            "description": "New Task Description",
            "group_id": str(mock_group_id),
            "assigned_student_ids": [str(mock_student_id)],
            "status": "pending", 
            "deadline": "2024-12-31T23:59:59Z"
        }
        
        response = client.post("/tasks/", json=task_data)
        assert response.status_code == 404
        assert "Student" in response.json()["detail"]

class TestGetAllTasks:
    @patch("models.task_model.Task.find_all")
    def test_get_all_tasks_success(self, mock_find_all, mock_current_user):
        # Setup mock task list
        mock_task_list = MagicMock()
        mock_task_list.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[mock_task])
        mock_find_all.return_value = mock_task_list
        
        # Setup mock links
        mock_task.group.fetch = AsyncMock(return_value=mock_group)
        mock_student_link = MagicMock()
        mock_student_link.fetch = AsyncMock(return_value=mock_student)
        mock_task.assigned_students = [mock_student_link]
        
        response = client.get("/tasks/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("models.task_model.Task.find_all")
    def test_get_all_tasks_with_pagination(self, mock_find_all, mock_current_user):
        mock_task_list = MagicMock()
        mock_task_list.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
        mock_find_all.return_value = mock_task_list
        
        response = client.get("/tasks/?skip=10&limit=5")
        assert response.status_code == 200
        mock_task_list.skip.assert_called_with(10)
        mock_task_list.skip.return_value.limit.assert_called_with(5)

class TestGetTask:
    @patch("models.task_model.Task.get")
    def test_get_task_success(self, mock_task_get, mock_current_user):
        mock_task_get.return_value = mock_task
        mock_task.group.fetch = AsyncMock(return_value=mock_group)
        mock_student_link = MagicMock()
        mock_student_link.fetch = AsyncMock(return_value=mock_student)
        mock_task.assigned_students = [mock_student_link]
        
        response = client.get(f"/tasks/{mock_task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == str(mock_task_id)

    @patch("models.task_model.Task.get")
    def test_get_task_not_found(self, mock_task_get, mock_current_user):
        mock_task_get.return_value = None
        
        response = client.get(f"/tasks/{mock_task_id}")
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_get_task_invalid_id(self, mock_current_user):
        response = client.get("/tasks/invalid_id")
        assert response.status_code == 400
        assert "Invalid task ID format" in response.json()["detail"]

class TestUpdateTask:
    @patch("models.task_model.Task.get")
    @patch("models.group_model.Group.get")
    @patch("models.user_model.User.get")
    @patch("models.task_model.Task.save")
    async def test_update_task_success(self, mock_task_save, mock_user_get, mock_group_get, mock_task_get, mock_current_user):
        # Setup mocks
        mock_task_get.return_value = mock_task
        mock_group_get.return_value = mock_group
        mock_group.project.fetch = AsyncMock(return_value=mock_project)
        mock_user_get.return_value = mock_student
        mock_task_save.return_value = None
        
        # Mock existing assigned students
        mock_task.assigned_students = [Link(mock_student, document_class=User)]
        
        task_data = {
            "title": "Updated Task",
            "description": "Updated Description",
            "group_id": str(mock_group_id),
            "assigned_student_ids": [str(mock_student_id)],
            "status": "completed",
            "deadline": "2024-12-31T23:59:59Z",
            "priority": "Low"
        }
        
        response = client.put(f"/tasks/{mock_task_id}", json=task_data)
        assert response.status_code == 200

    @patch("models.task_model.Task.get")
    def test_update_task_not_found(self, mock_task_get, mock_current_user):
        mock_task_get.return_value = None
        
        task_data = {
            "title": "Updated Task",
            "description": "Updated Description",
            "group_id": str(mock_group_id),
            "assigned_student_ids": [str(mock_student_id)],
            "status": "completed",
            "deadline": "2024-12-31T23:59:59Z"
        }
        
        response = client.put(f"/tasks/{mock_task_id}", json=task_data)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestDeleteTask:
    @patch("models.task_model.Task.get")
    @patch("models.task_model.Task.delete")
    @patch("models.group_model.Group.save")
    async def test_delete_task_success(self, mock_group_save, mock_task_delete, mock_task_get, mock_current_user):
        # Setup mocks
        mock_task_get.return_value = mock_task
        mock_task.group.fetch = AsyncMock(return_value=mock_group)
        mock_group.fetch_link = AsyncMock(return_value=[])
        mock_task_delete.return_value = None
        mock_group_save.return_value = None
        
        response = client.delete(f"/tasks/{mock_task_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Task deleted"

    @patch("models.task_model.Task.get")
    def test_delete_task_not_found(self, mock_task_get, mock_current_user):
        mock_task_get.return_value = None
        
        response = client.delete(f"/tasks/{mock_task_id}")
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    @patch("models.task_model.Task.get")
    async def test_delete_task_group_not_found(self, mock_task_get, mock_current_user):
        mock_task_copy = mock_task.copy()
        mock_task_copy.group = None
        mock_task_get.return_value = mock_task_copy
        
        response = client.delete(f"/tasks/{mock_task_id}")
        assert response.status_code == 404

class TestTaskRouteErrors:
    def test_create_task_internal_error(self, mock_current_user):
        with patch("models.group_model.Group.get", side_effect=Exception("Database error")):
            task_data = {
                "title": "New Task",
                "description": "New Task Description",
                "group_id": str(mock_group_id),
                "assigned_student_ids": [str(mock_student_id)],
                "status": "pending",
                "deadline": "2024-12-31T23:59:59Z"
            }
            
            response = client.post("/tasks/", json=task_data)
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_get_all_tasks_internal_error(self, mock_current_user):
        with patch("models.task_model.Task.find_all", side_effect=Exception("Database error")):
            response = client.get("/tasks/")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_get_task_internal_error(self, mock_current_user):
        with patch("models.task_model.Task.get", side_effect=Exception("Database error")):
            response = client.get(f"/tasks/{mock_task_id}")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_update_task_internal_error(self, mock_current_user):
        with patch("models.task_model.Task.get", side_effect=Exception("Database error")):
            task_data = {
                "title": "Updated Task",
                "description": "Updated Description",
                "group_id": str(mock_group_id),
                "assigned_student_ids": [str(mock_student_id)],
                "status": "completed",
                "deadline": "2024-12-31T23:59:59Z"
            }
            
            response = client.put(f"/tasks/{mock_task_id}", json=task_data)
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_delete_task_internal_error(self, mock_current_user):
        with patch("models.task_model.Task.get", side_effect=Exception("Database error")):
            response = client.delete(f"/tasks/{mock_task_id}")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

# Integration tests
class TestTaskRouteIntegration:
    """Integration tests that test the full flow"""
    
    @patch("models.task_model.Task.save")
    @patch("models.group_model.Group.save")
    @patch("models.group_model.Group.get")
    @patch("models.user_model.User.get")
    @patch("models.task_model.Task.get")
    async def test_full_task_lifecycle(self, mock_task_get, mock_user_get, mock_group_get, 
                                     mock_group_save, mock_task_save, mock_current_user):
        """Test creating, reading, updating, and deleting a task"""
        
        # Setup mocks for create
        mock_group_get.return_value = mock_group
        mock_group.project.fetch = AsyncMock(return_value=mock_project)
        mock_user_get.return_value = mock_student
        mock_group.fetch_link = AsyncMock(return_value=[])
        mock_task_save.return_value = None
        mock_group_save.return_value = None
        
        # 1. Create task
        task_data = {
            "title": "Lifecycle Task",
            "description": "Test lifecycle",
            "group_id": str(mock_group_id),
            "assigned_student_ids": [str(mock_student_id)],
            "status": "pending",
            "deadline": "2024-12-31T23:59:59Z",
            "priority": "Medium"
        }
        
        with patch("models.task_model.Task.__init__", return_value=None):
            with patch("models.task_model.Task.id", mock_task_id):
                create_response = client.post("/tasks/", json=task_data)
        
        assert create_response.status_code == 200
        
        # 2. Read task
        mock_task_get.return_value = mock_task
        mock_task.group.fetch = AsyncMock(return_value=mock_group)
        mock_student_link = MagicMock()
        mock_student_link.fetch = AsyncMock(return_value=mock_student)
        mock_task.assigned_students = [mock_student_link]
        
        read_response = client.get(f"/tasks/{mock_task_id}")
        assert read_response.status_code == 200
        
        # 3. Update task
        update_data = task_data.copy()
        update_data["title"] = "Updated Lifecycle Task"
        update_data["status"] = "completed"
        
        update_response = client.put(f"/tasks/{mock_task_id}", json=update_data)
        assert update_response.status_code == 200
        
        # 4. Delete task
        with patch("models.task_model.Task.delete", return_value=None):
            delete_response = client.delete(f"/tasks/{mock_task_id}")
        
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Task deleted"

if __name__ == "__main__":
    pytest.main([__file__])