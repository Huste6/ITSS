import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch, AsyncMock
from bson import ObjectId

@pytest.fixture
def mock_group():
    """Mock group data"""
    return {
        "id": str(ObjectId()),
        "name": "Test Group",
        "project_id": str(ObjectId()),
        "leader_id": str(ObjectId()),
        "members": [],
        "github_link": "https://github.com/test/repo"
    }

@pytest.fixture
def mock_project():
    """Mock project data"""
    return {
        "id": str(ObjectId()),
        "title": "Test Project",
        "description": "Test project description",
        "mentor_id": str(ObjectId())
    }

@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "id": str(ObjectId()),
        "ho_ten": "Test User",
        "email": "test@example.com",
        "role": "student",
        "group_id": None
    }

@pytest.mark.asyncio
async def test_create_group_success(test_app: AsyncClient):
    """Test tạo group thành công"""
    # Mock authentication
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_mentor.role = "mentor"
        mock_auth.return_value = mock_mentor
        
        # Mock database operations
        with patch('models.project_model.Project.get') as mock_project_get, \
             patch('models.user_model.User.get') as mock_user_get, \
             patch('models.group_model.Group.insert') as mock_group_insert, \
             patch('models.project_model.Project.save') as mock_project_save, \
             patch('models.user_model.User.save') as mock_user_save:
            
            # Setup mocks
            mock_project = Mock()
            mock_project.id = ObjectId()
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_project.groups = []
            mock_project_get.return_value = mock_project
            
            mock_leader = Mock()
            mock_leader.id = ObjectId()
            mock_leader.ho_ten = "Test Leader"
            mock_leader.email = "leader@example.com"
            mock_leader.role = "student"
            mock_leader.group_id = None
            mock_user_get.return_value = mock_leader
            
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.name = "Test Group"
            mock_group.members = []
            mock_group_insert.return_value = mock_group
            
            payload = {
                "name": "Test Group",
                "project_id": str(mock_project.id),
                "leader_id": str(mock_leader.id)
            }
            
            res = await test_app.post("/groups/", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["name"] == "Test Group"
            assert data["project_title"] == "Test Project"
            assert data["leader_name"] == "Test Leader"

@pytest.mark.asyncio
async def test_create_group_project_not_found(test_app: AsyncClient):
    """Test tạo group với project không tồn tại"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.project_model.Project.get', return_value=None):
            payload = {
                "name": "Test Group",
                "project_id": str(ObjectId()),
                "leader_id": str(ObjectId())
            }
            
            res = await test_app.post("/groups/", json=payload)
            assert res.status_code == 404
            assert res.json()["detail"] == "Project not found"

@pytest.mark.asyncio
async def test_create_group_leader_not_found(test_app: AsyncClient):
    """Test tạo group với leader không tồn tại"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.project_model.Project.get') as mock_project_get, \
             patch('models.user_model.User.get', return_value=None):
            
            mock_project = Mock()
            mock_project.id = ObjectId()
            mock_project_get.return_value = mock_project
            
            payload = {
                "name": "Test Group",
                "project_id": str(mock_project.id),
                "leader_id": str(ObjectId())
            }
            
            res = await test_app.post("/groups/", json=payload)
            assert res.status_code == 404
            assert res.json()["detail"] == "Leader not found"

@pytest.mark.asyncio
async def test_create_group_leader_not_student(test_app: AsyncClient):
    """Test tạo group với leader không phải student"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.project_model.Project.get') as mock_project_get, \
             patch('models.user_model.User.get') as mock_user_get:
            
            mock_project = Mock()
            mock_project.id = ObjectId()
            mock_project_get.return_value = mock_project
            
            mock_leader = Mock()
            mock_leader.id = ObjectId()
            mock_leader.role = "mentor"  # Not student
            mock_leader.group_id = None
            mock_user_get.return_value = mock_leader
            
            payload = {
                "name": "Test Group",
                "project_id": str(mock_project.id),
                "leader_id": str(mock_leader.id)
            }
            
            res = await test_app.post("/groups/", json=payload)
            assert res.status_code == 400
            assert res.json()["detail"] == "Leader must be a student"

@pytest.mark.asyncio
async def test_create_group_leader_already_in_group(test_app: AsyncClient):
    """Test tạo group với leader đã có group"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.project_model.Project.get') as mock_project_get, \
             patch('models.user_model.User.get') as mock_user_get:
            
            mock_project = Mock()
            mock_project.id = ObjectId()
            mock_project_get.return_value = mock_project
            
            mock_leader = Mock()
            mock_leader.id = ObjectId()
            mock_leader.role = "student"
            mock_leader.group_id = ObjectId()  # Already in group
            mock_user_get.return_value = mock_leader
            
            payload = {
                "name": "Test Group",
                "project_id": str(mock_project.id),
                "leader_id": str(mock_leader.id)
            }
            
            res = await test_app.post("/groups/", json=payload)
            assert res.status_code == 400
            assert res.json()["detail"] == "Leader is already in another group"

@pytest.mark.asyncio
async def test_get_group_by_id_success(test_app: AsyncClient):
    """Test lấy thông tin group theo ID thành công"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        with patch('models.group_model.Group.get') as mock_group_get:
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.name = "Test Group"
            mock_group.github_link = "https://github.com/test/repo"
            
            # Mock project
            mock_project = Mock()
            mock_project.id = ObjectId()
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_group.project.fetch = AsyncMock(return_value=mock_project)
            
            # Mock leader
            mock_leader = Mock()
            mock_leader.id = ObjectId()
            mock_leader.ho_ten = "Test Leader"
            mock_leader.email = "leader@example.com"
            mock_group.leaders.fetch = AsyncMock(return_value=mock_leader)
            
            # Mock members
            mock_member = Mock()
            mock_member.id = ObjectId()
            mock_member.ho_ten = "Test Member"
            mock_member.email = "member@example.com"
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=mock_member)
            mock_group.members = [mock_member_link]
            
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            res = await test_app.get(f"/groups/{group_id}")
            assert res.status_code == 200
            data = res.json()
            assert data["name"] == "Test Group"
            assert data["project_title"] == "Test Project"
            assert data["leader_name"] == "Test Leader"
            assert data["github_link"] == "https://github.com/test/repo"

@pytest.mark.asyncio
async def test_get_group_by_id_not_found(test_app: AsyncClient):
    """Test lấy group không tồn tại"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        with patch('models.group_model.Group.get', return_value=None):
            group_id = str(ObjectId())
            res = await test_app.get(f"/groups/{group_id}")
            assert res.status_code == 404
            assert res.json()["detail"] == "Group not found"

@pytest.mark.asyncio
async def test_get_group_by_id_invalid_format(test_app: AsyncClient):
    """Test lấy group với ID format không hợp lệ"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        res = await test_app.get("/groups/invalid_id")
        assert res.status_code == 400
        assert res.json()["detail"] == "Invalid group_id format"

@pytest.mark.asyncio
async def test_get_all_groups_success(test_app: AsyncClient):
    """Test lấy tất cả groups thành công"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        with patch('models.group_model.Group.find') as mock_find:
            # Mock group data
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.name = "Test Group"
            mock_group.github_link = "https://github.com/test/repo"
            
            # Mock project
            mock_project = Mock()
            mock_project.id = ObjectId()
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_group.project.fetch = AsyncMock(return_value=mock_project)
            
            # Mock leader
            mock_leader = Mock()
            mock_leader.id = ObjectId()
            mock_leader.ho_ten = "Test Leader"
            mock_leader.email = "leader@example.com"
            mock_group.leaders.fetch = AsyncMock(return_value=mock_leader)
            
            # Mock members
            mock_member = Mock()
            mock_member.id = ObjectId()
            mock_member.ho_ten = "Test Member"
            mock_member.email = "member@example.com"
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=mock_member)
            mock_group.members = [mock_member_link]
            
            # Setup find chain
            mock_query = Mock()
            mock_query.skip.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.to_list = AsyncMock(return_value=[mock_group])
            mock_find.return_value = mock_query
            
            res = await test_app.get("/groups/")
            assert res.status_code == 200
            data = res.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "Test Group"

@pytest.mark.asyncio
async def test_add_github_link_success(test_app: AsyncClient):
    """Test thêm GitHub link thành công"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.group_model.Group.save') as mock_save:
            
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.github_link = None
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            github_link = "https://github.com/test/repo"
            
            res = await test_app.post(f"/groups/add-github-link/{group_id}?github_link={github_link}")
            assert res.status_code == 200
            data = res.json()
            assert data["github_link"] == github_link
            assert mock_group.github_link == github_link
            mock_save.assert_called_once()

@pytest.mark.asyncio
async def test_add_github_link_group_not_found(test_app: AsyncClient):
    """Test thêm GitHub link với group không tồn tại"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        with patch('models.group_model.Group.get', return_value=None):
            group_id = str(ObjectId())
            github_link = "https://github.com/test/repo"
            
            res = await test_app.post(f"/groups/add-github-link/{group_id}?github_link={github_link}")
            assert res.status_code == 404
            assert res.json()["detail"] == "Group not found"

@pytest.mark.asyncio
async def test_add_member_to_group_success(test_app: AsyncClient):
    """Test thêm member vào group thành công"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.user_model.User.get') as mock_user_get, \
             patch('models.user_model.User.save') as mock_user_save, \
             patch('models.group_model.Group.save') as mock_group_save:
            
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.members = []
            mock_group_get.return_value = mock_group
            
            mock_member = Mock()
            mock_member.id = ObjectId()
            mock_member.group_id = None
            mock_user_get.return_value = mock_member
            
            group_id = str(mock_group.id)
            member_id = str(mock_member.id)
            
            res = await test_app.post(f"/groups/{group_id}/add-member/{member_id}")
            assert res.status_code == 200
            assert res.json() == True
            mock_user_save.assert_called_once()
            mock_group_save.assert_called_once()

@pytest.mark.asyncio
async def test_add_member_already_in_group(test_app: AsyncClient):
    """Test thêm member đã có group"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.user_model.User.get') as mock_user_get:
            
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group_get.return_value = mock_group
            
            mock_member = Mock()
            mock_member.id = ObjectId()
            mock_member.group_id = ObjectId()  # Already in group
            mock_user_get.return_value = mock_member
            
            group_id = str(mock_group.id)
            member_id = str(mock_member.id)
            
            res = await test_app.post(f"/groups/{group_id}/add-member/{member_id}")
            assert res.status_code == 400
            assert res.json()["detail"] == "Member is already in another group"

@pytest.mark.asyncio
async def test_change_group_leader_success(test_app: AsyncClient):
    """Test thay đổi leader group thành công"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.user_model.User.get') as mock_user_get, \
             patch('models.group_model.Group.save') as mock_group_save:
            
            # Mock new leader
            new_leader_id = ObjectId()
            mock_new_leader = Mock()
            mock_new_leader.id = new_leader_id
            mock_new_leader.ho_ten = "New Leader"
            mock_new_leader.role = "student"
            mock_user_get.return_value = mock_new_leader
            
            # Mock existing member
            mock_member = Mock()
            mock_member.id = new_leader_id
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=mock_member)
            
            # Mock group
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.name = "Test Group"
            mock_group.members = [mock_member_link]
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            new_leader_id_str = str(new_leader_id)
            
            res = await test_app.put(f"/groups/{group_id}/change-leader/{new_leader_id_str}")
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == "Leader changed successfully"
            assert data["new_leader_name"] == "New Leader"
            mock_group_save.assert_called_once()

@pytest.mark.asyncio
async def test_change_leader_not_member(test_app: AsyncClient):
    """Test thay đổi leader với user không phải member"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.user_model.User.get') as mock_user_get:
            
            # Mock new leader (not in group)
            new_leader_id = ObjectId()
            mock_new_leader = Mock()
            mock_new_leader.id = new_leader_id
            mock_new_leader.role = "student"
            mock_user_get.return_value = mock_new_leader
            
            # Mock group with different member
            mock_member = Mock()
            mock_member.id = ObjectId()  # Different ID
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=mock_member)
            
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.members = [mock_member_link]
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            new_leader_id_str = str(new_leader_id)
            
            res = await test_app.put(f"/groups/{group_id}/change-leader/{new_leader_id_str}")
            assert res.status_code == 400
            assert res.json()["detail"] == "New leader is not a member of the group"

@pytest.mark.asyncio
async def test_remove_member_from_group_success(test_app: AsyncClient):
    """Test xóa member khỏi group thành công"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.user_model.User.get') as mock_user_get, \
             patch('models.group_model.Group.save') as mock_group_save, \
             patch('models.user_model.User.save') as mock_user_save:
            
            # Mock member to remove
            member_id = ObjectId()
            mock_member = Mock()
            mock_member.id = member_id
            mock_member.group_id = ObjectId()
            mock_user_get.return_value = mock_member
            
            # Mock member link
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=mock_member)
            
            # Mock group
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.name = "Test Group"
            mock_group.members = [mock_member_link]
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            member_id_str = str(member_id)
            
            res = await test_app.delete(f"/groups/{group_id}/remove-member/{member_id_str}")
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == "Member removed successfully"
            assert mock_member.group_id is None
            mock_group_save.assert_called_once()
            mock_user_save.assert_called_once()

@pytest.mark.asyncio
async def test_remove_member_not_in_group(test_app: AsyncClient):
    """Test xóa member không có trong group"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.user_model.User.get') as mock_user_get:
            
            # Mock member to remove (not in group)
            member_id = ObjectId()
            mock_member = Mock()
            mock_member.id = member_id
            mock_user_get.return_value = mock_member
            
            # Mock different member in group
            different_member = Mock()
            different_member.id = ObjectId()  # Different ID
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=different_member)
            
            # Mock group
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.members = [mock_member_link]
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            member_id_str = str(member_id)
            
            res = await test_app.delete(f"/groups/{group_id}/remove-member/{member_id_str}")
            assert res.status_code == 400
            assert res.json()["detail"] == "Member is not in the group"

@pytest.mark.asyncio
async def test_delete_group_success(test_app: AsyncClient):
    """Test xóa group thành công"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get') as mock_group_get, \
             patch('models.group_model.Group.delete') as mock_group_delete, \
             patch('models.user_model.User.save') as mock_user_save:
            
            # Mock member
            mock_member = Mock()
            mock_member.id = ObjectId()
            mock_member.group_id = ObjectId()
            mock_member_link = Mock()
            mock_member_link.fetch = AsyncMock(return_value=mock_member)
            
            # Mock group
            mock_group = Mock()
            mock_group.id = ObjectId()
            mock_group.members = [mock_member_link]
            mock_group.fetch_link = AsyncMock(return_value=[])  # No tasks
            mock_group_get.return_value = mock_group
            
            group_id = str(mock_group.id)
            
            res = await test_app.delete(f"/groups/{group_id}")
            assert res.status_code == 200
            data = res.json()
            assert data["message"] == "Group deleted"
            assert mock_member.group_id is None
            mock_group_delete.assert_called_once()
            mock_user_save.assert_called_once()

@pytest.mark.asyncio
async def test_delete_group_not_found(test_app: AsyncClient):
    """Test xóa group không tồn tại"""
    with patch('routes.user_routes.get_current_mentor') as mock_auth:
        mock_mentor = Mock()
        mock_mentor.id = ObjectId()
        mock_auth.return_value = mock_mentor
        
        with patch('models.group_model.Group.get', return_value=None):
            group_id = str(ObjectId())
            
            res = await test_app.delete(f"/groups/{group_id}")
            assert res.status_code == 404
            assert res.json()["detail"] == "Group not found"

@pytest.mark.asyncio
async def test_invalid_group_id_format(test_app: AsyncClient):
    """Test các endpoint với group_id format không hợp lệ"""
    with patch('routes.user_routes.get_current_user') as mock_auth:
        mock_user = Mock()
        mock_user.id = ObjectId()
        mock_auth.return_value = mock_user
        
        invalid_id = "invalid_id_format"
        
        # Test get group
        res = await test_app.get(f"/groups/{invalid_id}")
        assert res.status_code == 400
        assert res.json()["detail"] == "Invalid group_id format"
        
        # Test add github link
        res = await test_app.post(f"/groups/add-github-link/{invalid_id}?github_link=test")
        assert res.status_code == 400
        assert res.json()["detail"] == "Invalid group_id format"