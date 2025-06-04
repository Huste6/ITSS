import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from bson import ObjectId

class TestEvaluationRouter:
    
    @pytest.fixture
    async def setup_test_data(self, test_app: AsyncClient):
        """Setup test data: users and project"""
        # Create evaluator (mentor/admin)
        evaluator_payload = {
            "HoDem": "Nguyen",
            "Ten": "Mentor",
            "email": "mentor@example.com",
            "password": "mentorpass123",
            "role": "mentor",
            "github_user": "mentor_user"
        }
        evaluator_res = await test_app.post("/users/register", json=evaluator_payload)
        evaluator_data = evaluator_res.json()
        
        # Create student
        student_payload = {
            "HoDem": "Le",
            "Ten": "Student",
            "email": "student@example.com",
            "password": "studentpass123",
            "role": "student",
            "github_user": "student_user"
        }
        student_res = await test_app.post("/users/register", json=student_payload)
        student_data = student_res.json()
        
        # Login evaluator to get token
        login_data = {
            "username": "mentor@example.com",
            "password": "mentorpass123"
        }
        login_res = await test_app.post("/users/login", data=login_data)
        token = login_res.json()["access_token"]
        
        return {
            "evaluator": evaluator_data,
            "student": student_data,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

    @pytest.mark.asyncio
    async def test_create_evaluation_success(self, test_app: AsyncClient, setup_test_data):
        """Test tạo evaluation thành công"""
        test_data = await setup_test_data
        
        # Mock project data (assuming project exists)
        project_id = str(ObjectId())
        
        with patch('routes.evaluation_routes.Project.get') as mock_project_get, \
             patch('routes.evaluation_routes.User.get') as mock_user_get, \
             patch('routes.evaluation_routes.Evaluation.insert') as mock_insert:
            
            # Mock project
            mock_project = AsyncMock()
            mock_project.id = ObjectId(project_id)
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_project_get.return_value = mock_project
            
            # Mock student
            mock_student = AsyncMock()
            mock_student.id = ObjectId(test_data["student"]["id"])
            mock_student.ho_ten = test_data["student"]["ho_ten"]
            mock_student.email = test_data["student"]["email"]
            mock_user_get.return_value = mock_student
            
            # Mock evaluation insert
            mock_evaluation = AsyncMock()
            mock_evaluation.id = ObjectId()
            mock_evaluation.score = 8.5
            mock_evaluation.comment = "Good work"
            mock_insert.return_value = None
            
            evaluation_payload = {
                "student_id": test_data["student"]["id"],
                "project_id": project_id,
                "score": 8.5,
                "comment": "Good work"
            }
            
            res = await test_app.post(
                "/evaluations/",
                json=evaluation_payload,
                headers=test_data["headers"]
            )
            
            assert res.status_code == 200
            data = res.json()
            assert data["score"] == 8.5
            assert data["comment"] == "Good work"
            assert "student" in data
            assert "project" in data
            assert "evaluator" in data

    @pytest.mark.asyncio
    async def test_create_evaluation_invalid_student(self, test_app: AsyncClient, setup_test_data):
        """Test tạo evaluation với student không tồn tại"""
        test_data = await setup_test_data
        
        with patch('routes.evaluation_routes.User.get') as mock_user_get:
            mock_user_get.return_value = None
            
            evaluation_payload = {
                "student_id": str(ObjectId()),
                "project_id": str(ObjectId()),
                "score": 8.5,
                "comment": "Good work"
            }
            
            res = await test_app.post(
                "/evaluations/",
                json=evaluation_payload,
                headers=test_data["headers"]
            )
            
            assert res.status_code == 500  # Internal server error due to student not found

    @pytest.mark.asyncio
    async def test_create_evaluation_invalid_project(self, test_app: AsyncClient, setup_test_data):
        """Test tạo evaluation với project không tồn tại"""
        test_data = await setup_test_data
        
        with patch('routes.evaluation_routes.Project.get') as mock_project_get, \
             patch('routes.evaluation_routes.User.get') as mock_user_get:
            
            mock_project_get.return_value = None
            
            # Mock student exists
            mock_student = AsyncMock()
            mock_student.id = ObjectId(test_data["student"]["id"])
            mock_user_get.return_value = mock_student
            
            evaluation_payload = {
                "student_id": test_data["student"]["id"],
                "project_id": str(ObjectId()),
                "score": 8.5,
                "comment": "Good work"
            }
            
            res = await test_app.post(
                "/evaluations/",
                json=evaluation_payload,
                headers=test_data["headers"]
            )
            
            assert res.status_code == 404
            assert res.json()["detail"] == "Project not found"

    @pytest.mark.asyncio
    async def test_create_evaluation_unauthorized(self, test_app: AsyncClient):
        """Test tạo evaluation mà không có token"""
        evaluation_payload = {
            "student_id": str(ObjectId()),
            "project_id": str(ObjectId()),
            "score": 8.5,
            "comment": "Good work"
        }
        
        res = await test_app.post("/evaluations/", json=evaluation_payload)
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_get_all_evaluations(self, test_app: AsyncClient, setup_test_data):
        """Test lấy tất cả evaluations"""
        test_data = await setup_test_data
        
        with patch('routes.evaluation_routes.Evaluation.find') as mock_find:
            # Mock evaluation data
            mock_evaluation = AsyncMock()
            mock_evaluation.id = ObjectId()
            mock_evaluation.score = 8.5
            mock_evaluation.comment = "Good work"
            
            # Mock evaluator link
            mock_evaluator = AsyncMock()
            mock_evaluator.id = ObjectId()
            mock_evaluator.ho_ten = "Nguyen Mentor"
            mock_evaluator.email = "mentor@example.com"
            mock_evaluation.evaluator.fetch.return_value = mock_evaluator
            
            # Mock student link
            mock_student = AsyncMock()
            mock_student.id = ObjectId()
            mock_student.ho_ten = "Le Student"
            mock_student.email = "student@example.com"
            mock_evaluation.student.fetch.return_value = mock_student
            
            # Mock project link
            mock_project = AsyncMock()
            mock_project.id = ObjectId()
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_evaluation.project.fetch.return_value = mock_project
            
            # Mock find query
            mock_query = AsyncMock()
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list.return_value = [mock_evaluation]
            mock_find.return_value = mock_query
            
            res = await test_app.get("/evaluations/", headers=test_data["headers"])
            
            assert res.status_code == 200
            data = res.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_evaluation_by_id(self, test_app: AsyncClient, setup_test_data):
        """Test lấy evaluation theo ID"""
        test_data = await setup_test_data
        evaluation_id = str(ObjectId())
        
        with patch('routes.evaluation_routes.Evaluation.get') as mock_get:
            # Mock evaluation
            mock_evaluation = AsyncMock()
            mock_evaluation.id = ObjectId(evaluation_id)
            mock_evaluation.score = 8.5
            mock_evaluation.comment = "Good work"
            
            # Mock links
            mock_evaluator = AsyncMock()
            mock_evaluator.id = ObjectId()
            mock_evaluator.ho_ten = "Nguyen Mentor"
            mock_evaluator.email = "mentor@example.com"
            mock_evaluation.evaluator.fetch.return_value = mock_evaluator
            
            mock_student = AsyncMock()
            mock_student.id = ObjectId()
            mock_student.ho_ten = "Le Student"
            mock_student.email = "student@example.com"
            mock_evaluation.student.fetch.return_value = mock_student
            
            mock_project = AsyncMock()
            mock_project.id = ObjectId()
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_evaluation.project.fetch.return_value = mock_project
            
            mock_get.return_value = mock_evaluation
            
            res = await test_app.get(f"/evaluations/{evaluation_id}", headers=test_data["headers"])
            
            assert res.status_code == 200
            data = res.json()
            assert data["score"] == 8.5
            assert data["comment"] == "Good work"

    @pytest.mark.asyncio
    async def test_get_evaluation_not_found(self, test_app: AsyncClient, setup_test_data):
        """Test lấy evaluation không tồn tại"""
        test_data = await setup_test_data
        evaluation_id = str(ObjectId())
        
        with patch('routes.evaluation_routes.Evaluation.get') as mock_get:
            mock_get.return_value = None
            
            res = await test_app.get(f"/evaluations/{evaluation_id}", headers=test_data["headers"])
            
            assert res.status_code == 404
            assert res.json()["detail"] == "Evaluation not found"

    @pytest.mark.asyncio
    async def test_get_evaluation_invalid_id(self, test_app: AsyncClient, setup_test_data):
        """Test lấy evaluation với ID không hợp lệ"""
        test_data = await setup_test_data
        invalid_id = "invalid_id"
        
        res = await test_app.get(f"/evaluations/{invalid_id}", headers=test_data["headers"])
        
        assert res.status_code == 400
        assert res.json()["detail"] == "Invalid evaluation_id format"

    @pytest.mark.asyncio
    async def test_update_evaluation_success(self, test_app: AsyncClient, setup_test_data):
        """Test cập nhật evaluation thành công"""
        test_data = await setup_test_data
        evaluation_id = str(ObjectId())
        
        with patch('routes.evaluation_routes.Evaluation.get') as mock_get, \
             patch('routes.evaluation_routes.User.get') as mock_user_get, \
             patch('routes.evaluation_routes.Project.get') as mock_project_get:
            
            # Mock existing evaluation
            mock_evaluation = AsyncMock()
            mock_evaluation.id = ObjectId(evaluation_id)
            mock_evaluation.score = 7.0
            mock_evaluation.comment = "Old comment"
            
            # Mock evaluator (current user)
            mock_evaluator = AsyncMock()
            mock_evaluator.id = ObjectId()
            mock_evaluation.evaluator = mock_evaluator
            mock_evaluation.evaluator.fetch.return_value = mock_evaluator
            
            mock_get.return_value = mock_evaluation
            
            # Mock student and project
            mock_student = AsyncMock()
            mock_student.id = ObjectId(test_data["student"]["id"])
            mock_student.ho_ten = test_data["student"]["ho_ten"]
            mock_user_get.return_value = mock_student
            
            mock_project = AsyncMock()
            mock_project.id = ObjectId()
            mock_project.title = "Updated Project"
            mock_project_get.return_value = mock_project
            
            # Mock save
            mock_evaluation.save = AsyncMock()
            
            update_payload = {
                "student_id": test_data["student"]["id"],
                "project_id": str(mock_project.id),
                "score": 9.0,
                "comment": "Updated comment"
            }
            
            res = await test_app.put(
                f"/evaluations/{evaluation_id}",
                json=update_payload,
                headers=test_data["headers"]
            )
            
            assert res.status_code == 200
            data = res.json()
            assert data["score"] == 9.0
            assert data["comment"] == "Updated comment"

    @pytest.mark.asyncio
    async def test_delete_evaluation_success(self, test_app: AsyncClient, setup_test_data):
        """Test xóa evaluation thành công"""
        test_data = await setup_test_data
        evaluation_id = str(ObjectId())
        
        with patch('routes.evaluation_routes.Evaluation.get') as mock_get:
            # Mock evaluation
            mock_evaluation = AsyncMock()
            mock_evaluation.id = ObjectId(evaluation_id)
            
            # Mock evaluator
            mock_evaluator = AsyncMock()
            mock_evaluator.id = ObjectId()
            mock_evaluation.evaluator = mock_evaluator
            mock_evaluation.evaluator.fetch.return_value = mock_evaluator
            
            # Mock delete
            mock_evaluation.delete = AsyncMock()
            
            mock_get.return_value = mock_evaluation
            
            res = await test_app.delete(f"/evaluations/{evaluation_id}", headers=test_data["headers"])
            
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == "Evaluation deleted"

    @pytest.mark.asyncio
    async def test_delete_evaluation_not_found(self, test_app: AsyncClient, setup_test_data):
        """Test xóa evaluation không tồn tại"""
        test_data = await setup_test_data
        evaluation_id = str(ObjectId())
        
        with patch('routes.evaluation_routes.Evaluation.get') as mock_get:
            mock_get.return_value = None
            
            res = await test_app.delete(f"/evaluations/{evaluation_id}", headers=test_data["headers"])
            
            assert res.status_code == 404
            assert res.json()["detail"] == "Evaluation not found"

    @pytest.mark.asyncio
    async def test_evaluation_pagination(self, test_app: AsyncClient, setup_test_data):
        """Test phân trang evaluations"""
        test_data = await setup_test_data
        
        with patch('routes.evaluation_routes.Evaluation.find') as mock_find:
            # Mock empty list
            mock_query = AsyncMock()
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list.return_value = []
            mock_find.return_value = mock_query
            
            # Test with pagination parameters
            res = await test_app.get(
                "/evaluations/?skip=0&limit=5",
                headers=test_data["headers"]
            )
            
            assert res.status_code == 200
            data = res.json()
            assert isinstance(data, list)
            
            # Verify pagination was called
            mock_query.skip.assert_called_with(0)
            mock_query.limit.assert_called_with(5)