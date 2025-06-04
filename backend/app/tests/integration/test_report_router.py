import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId
from beanie import Link

# Import your main app and models
from main import app  # Adjust import path as needed
from models.report_model import Report
from models.task_model import Task
from models.user_model import User
from schemas.pyobjectid_schemas import PyObjectId

client = TestClient(app)

# Mock data
mock_user_id = ObjectId()
mock_task_id = ObjectId()
mock_report_id = ObjectId()
mock_student_id = ObjectId()
mock_other_user_id = ObjectId()

mock_student = User(
    id=mock_student_id,
    ho_ten="Test Student",
    email="student@test.com",
    role="student"
)

mock_other_student = User(
    id=mock_other_user_id,
    ho_ten="Other Student", 
    email="other@test.com",
    role="student"
)

mock_admin = User(
    id=mock_user_id,
    ho_ten="Test Admin",
    email="admin@test.com",
    role="admin"
)

mock_task = Task(
    id=mock_task_id,
    title="Test Task",
    deadline=datetime.now(timezone.utc)
)

mock_report = Report(
    id=mock_report_id,
    content="Test Report Content",
    title="Test Report Title",
    student=Link(mock_student, document_class=User),
    task=Link(mock_task, document_class=Task),
    created_at=datetime.now(timezone.utc)
)

@pytest.fixture
def mock_current_student():
    with patch("routes.report_routes.get_current_user", return_value=mock_student):
        yield mock_student

@pytest.fixture
def mock_current_admin():
    with patch("routes.report_routes.get_current_user", return_value=mock_admin):
        yield mock_admin

@pytest.fixture
def mock_other_current_student():
    with patch("routes.report_routes.get_current_user", return_value=mock_other_student):
        yield mock_other_student

class TestCreateReport:
    @patch("models.report_model.Report.insert")
    @patch("models.task_model.Task.get")
    async def test_create_report_success(self, mock_task_get, mock_report_insert, mock_current_student):
        # Setup mocks
        mock_task_get.return_value = mock_task
        mock_report_insert.return_value = None
        
        # Mock the report creation
        with patch("models.report_model.Report") as mock_report_class:
            mock_report_instance = MagicMock()
            mock_report_instance.id = mock_report_id
            mock_report_instance.content = "Test Content"
            mock_report_instance.title = "Test Title"
            mock_report_instance.created_at = datetime.now(timezone.utc)
            mock_report_instance.student = Link(mock_student, document_class=User)
            mock_report_instance.task = Link(mock_task, document_class=Task)
            
            # Mock the Link fetch methods
            mock_report_instance.student.fetch = AsyncMock(return_value=mock_student)
            mock_report_instance.task.fetch = AsyncMock(return_value=mock_task)
            
            mock_report_class.return_value = mock_report_instance
            
            report_data = {
                "content": "Test Content",
                "title": "Test Title",
                "task_id": str(mock_task_id)
            }
            
            response = client.post("/reports/", json=report_data)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["content"] == "Test Content"
            assert "student" in response_data
            assert "task" in response_data

    @patch("models.task_model.Task.get")
    def test_create_report_task_not_found(self, mock_task_get, mock_current_student):
        mock_task_get.return_value = None
        
        report_data = {
            "content": "Test Content",
            "title": "Test Title", 
            "task_id": str(mock_task_id)
        }
        
        response = client.post("/reports/", json=report_data)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestGetReportById:
    @patch("models.report_model.Report.get")
    def test_get_report_success(self, mock_report_get, mock_current_student):
        mock_report_get.return_value = mock_report
        mock_report.task.fetch = AsyncMock(return_value=mock_task)
        
        response = client.get(f"/reports/{mock_report_id}")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["content"] == mock_report.content
        assert "task" in response_data

    @patch("models.report_model.Report.get")
    def test_get_report_not_found(self, mock_report_get, mock_current_student):
        mock_report_get.return_value = None
        
        response = client.get(f"/reports/{mock_report_id}")
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]

    def test_get_report_invalid_id(self, mock_current_student):
        response = client.get("/reports/invalid_id")
        assert response.status_code == 400
        assert "Invalid ObjectId format" in response.json()["detail"]

    @patch("models.report_model.Report.get")
    def test_get_report_task_not_found(self, mock_report_get, mock_current_student):
        mock_report_copy = MagicMock()
        mock_report_copy.id = mock_report_id
        mock_report_copy.content = "Test Content"
        mock_report_copy.created_at = datetime.now(timezone.utc)
        mock_report_copy.task.fetch = AsyncMock(return_value=None)
        mock_report_get.return_value = mock_report_copy
        
        response = client.get(f"/reports/{mock_report_id}")
        assert response.status_code == 404
        assert "Task associated with report not found" in response.json()["detail"]

class TestGetAllReports:
    @patch("models.report_model.Report.find_all")
    def test_get_all_reports_success(self, mock_find_all, mock_current_admin):
        # Setup mock report list
        mock_report_list = MagicMock()
        mock_report_list.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[mock_report])
        mock_find_all.return_value = mock_report_list
        
        # Setup mock links
        mock_report.task.fetch = AsyncMock(return_value=mock_task)
        
        response = client.get("/reports/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    @patch("models.report_model.Report.find_all")  
    def test_get_all_reports_with_pagination(self, mock_find_all, mock_current_admin):
        mock_report_list = MagicMock()
        mock_report_list.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
        mock_find_all.return_value = mock_report_list
        
        response = client.get("/reports/?skip=5&limit=20")
        assert response.status_code == 200
        mock_report_list.skip.assert_called_with(5)
        mock_report_list.skip.return_value.limit.assert_called_with(20)

    @patch("models.report_model.Report.find_all")
    def test_get_all_reports_empty(self, mock_find_all, mock_current_admin):
        mock_report_list = MagicMock()
        mock_report_list.skip.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
        mock_find_all.return_value = mock_report_list
        
        response = client.get("/reports/")
        assert response.status_code == 200
        assert response.json() == []

class TestUpdateReport:
    @patch("models.report_model.Report.save")
    @patch("models.task_model.Task.get")
    @patch("models.report_model.Report.get")
    async def test_update_report_success(self, mock_report_get, mock_task_get, mock_report_save, mock_current_student):
        # Setup mocks
        mock_report_get.return_value = mock_report
        mock_task_get.return_value = mock_task
        mock_report_save.return_value = None
        
        # Mock the student fetch
        mock_report.student.fetch = AsyncMock(return_value=mock_student)
        mock_report.task.fetch = AsyncMock(return_value=mock_task)
        
        report_data = {
            "content": "Updated Content",
            "title": "Updated Title",
            "task_id": str(mock_task_id)
        }
        
        response = client.put(f"/reports/{mock_report_id}", json=report_data)
        assert response.status_code == 200
        assert "Updated Content" in response.json()["content"]

    @patch("models.report_model.Report.get")
    def test_update_report_not_found(self, mock_report_get, mock_current_student):
        mock_report_get.return_value = None
        
        report_data = {
            "content": "Updated Content",
            "title": "Updated Title",
            "task_id": str(mock_task_id)
        }
        
        response = client.put(f"/reports/{mock_report_id}", json=report_data)
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]

    @patch("models.report_model.Report.get")
    async def test_update_report_unauthorized(self, mock_report_get, mock_other_current_student):
        # Setup report owned by different student
        mock_report_copy = MagicMock()
        mock_report_copy.id = mock_report_id
        mock_report_copy.student.fetch = AsyncMock(return_value=mock_student)  # Different student
        mock_report_get.return_value = mock_report_copy
        
        report_data = {
            "content": "Updated Content", 
            "title": "Updated Title",
            "task_id": str(mock_task_id)
        }
        
        response = client.put(f"/reports/{mock_report_id}", json=report_data)
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]

    @patch("models.task_model.Task.get")
    @patch("models.report_model.Report.get")
    async def test_update_report_task_not_found(self, mock_report_get, mock_task_get, mock_current_student):
        mock_report_get.return_value = mock_report
        mock_task_get.return_value = None
        mock_report.student.fetch = AsyncMock(return_value=mock_student)
        
        report_data = {
            "content": "Updated Content",
            "title": "Updated Title", 
            "task_id": str(mock_task_id)
        }
        
        response = client.put(f"/reports/{mock_report_id}", json=report_data)
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestDeleteReport:
    @patch("models.report_model.Report.delete")
    @patch("models.report_model.Report.get")
    async def test_delete_report_success(self, mock_report_get, mock_report_delete, mock_current_student):
        mock_report_get.return_value = mock_report
        mock_report_delete.return_value = None
        mock_report.student.fetch = AsyncMock(return_value=mock_student)
        
        response = client.delete(f"/reports/{mock_report_id}")
        assert response.status_code == 200
        assert response.json()["message"] == "Report deleted"

    @patch("models.report_model.Report.get")
    def test_delete_report_not_found(self, mock_report_get, mock_current_student):
        mock_report_get.return_value = None
        
        response = client.delete(f"/reports/{mock_report_id}")
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]

    def test_delete_report_invalid_id(self, mock_current_student):
        response = client.delete("/reports/invalid_id")
        assert response.status_code == 400
        assert "Invalid ObjectId format" in response.json()["detail"]

    @patch("models.report_model.Report.get")
    async def test_delete_report_unauthorized(self, mock_report_get, mock_other_current_student):
        mock_report_copy = MagicMock()
        mock_report_copy.id = mock_report_id
        mock_report_copy.student.fetch = AsyncMock(return_value=mock_student)  # Different student
        mock_report_get.return_value = mock_report_copy
        
        response = client.delete(f"/reports/{mock_report_id}")
        assert response.status_code == 403
        assert "Not authorized to delete this report" in response.json()["detail"]

class TestReportRouteErrors:
    def test_create_report_internal_error(self, mock_current_student):
        with patch("models.task_model.Task.get", side_effect=Exception("Database error")):
            report_data = {
                "content": "Test Content",
                "title": "Test Title",
                "task_id": str(mock_task_id)
            }
            
            response = client.post("/reports/", json=report_data)
            # Note: This might return 500 if you add try-catch in the actual route
            assert response.status_code in [404, 500]

    def test_get_report_internal_error(self, mock_current_student):
        with patch("models.report_model.Report.get", side_effect=Exception("Database error")):
            response = client.get(f"/reports/{mock_report_id}")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_get_all_reports_internal_error(self, mock_current_admin):
        with patch("models.report_model.Report.find_all", side_effect=Exception("Database error")):
            response = client.get("/reports/")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_update_report_internal_error(self, mock_current_student):
        with patch("models.report_model.Report.get", side_effect=Exception("Database error")):
            report_data = {
                "content": "Updated Content",
                "title": "Updated Title",
                "task_id": str(mock_task_id)
            }
            
            response = client.put(f"/reports/{mock_report_id}", json=report_data)
            # Note: This might return 500 if you add try-catch in the actual route
            assert response.status_code in [404, 500]

    def test_delete_report_internal_error(self, mock_current_student):
        with patch("models.report_model.Report.get", side_effect=Exception("Database error")):
            response = client.delete(f"/reports/{mock_report_id}")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

# Integration tests  
class TestReportRouteIntegration:
    """Integration tests that test the full flow"""
    
    @patch("models.report_model.Report.insert")
    @patch("models.report_model.Report.save")
    @patch("models.report_model.Report.delete")
    @patch("models.report_model.Report.get")
    @patch("models.task_model.Task.get")
    async def test_full_report_lifecycle(self, mock_task_get, mock_report_get, 
                                       mock_report_delete, mock_report_save, 
                                       mock_report_insert, mock_current_student):
        """Test creating, reading, updating, and deleting a report"""
        
        # Setup mocks
        mock_task_get.return_value = mock_task
        mock_report_insert.return_value = None
        mock_report_save.return_value = None
        mock_report_delete.return_value = None
        
        # 1. Create report
        report_data = {
            "content": "Lifecycle Report Content",
            "title": "Lifecycle Report Title",
            "task_id": str(mock_task_id)
        }
        
        with patch("models.report_model.Report") as mock_report_class:
            mock_report_instance = MagicMock()
            mock_report_instance.id = mock_report_id
            mock_report_instance.content = report_data["content"]
            mock_report_instance.title = report_data["title"]
            mock_report_instance.created_at = datetime.now(timezone.utc)
            mock_report_instance.student = Link(mock_student, document_class=User)
            mock_report_instance.task = Link(mock_task, document_class=Task)
            mock_report_instance.student.fetch = AsyncMock(return_value=mock_student)
            mock_report_instance.task.fetch = AsyncMock(return_value=mock_task)
            mock_report_class.return_value = mock_report_instance
            
            create_response = client.post("/reports/", json=report_data)
        
        assert create_response.status_code == 200
        
        # 2. Read report
        mock_report_get.return_value = mock_report
        mock_report.task.fetch = AsyncMock(return_value=mock_task)
        
        read_response = client.get(f"/reports/{mock_report_id}")
        assert read_response.status_code == 200
        
        # 3. Update report
        mock_report.student.fetch = AsyncMock(return_value=mock_student)
        mock_report.task.fetch = AsyncMock(return_value=mock_task)
        
        update_data = report_data.copy()
        update_data["content"] = "Updated Lifecycle Content"
        
        update_response = client.put(f"/reports/{mock_report_id}", json=update_data)
        assert update_response.status_code == 200
        
        # 4. Delete report
        delete_response = client.delete(f"/reports/{mock_report_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Report deleted"

class TestReportRouteValidation:
    """Test input validation and edge cases"""
    
    def test_create_report_missing_fields(self, mock_current_student):
        # Test with missing required fields
        incomplete_data = {
            "content": "Test Content"
            # Missing title and task_id
        }
        
        response = client.post("/reports/", json=incomplete_data)
        assert response.status_code == 422  # Validation error

    def test_get_all_reports_invalid_pagination(self, mock_current_admin):
        # Test with invalid pagination parameters
        response = client.get("/reports/?skip=-1&limit=200")
        assert response.status_code == 422  # Validation error

    @patch("models.task_model.Task.get")
    def test_create_report_empty_content(self, mock_task_get, mock_current_student):
        mock_task_get.return_value = mock_task
        
        report_data = {
            "content": "",
            "title": "Test Title",
            "task_id": str(mock_task_id)
        }
        
        # This test depends on your validation rules
        # You might want to add validation for empty content
        response = client.post("/reports/", json=report_data)
        # Adjust expected status code based on your validation rules
        assert response.status_code in [200, 422]

if __name__ == "__main__":
    pytest.main([__file__])