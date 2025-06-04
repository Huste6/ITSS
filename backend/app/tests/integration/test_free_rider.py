import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from fastapi import HTTPException
from bson import ObjectId

# Import the function and dependencies
from routes.free_rider import get_free_rider, get_github_service
from models.free_rider import FreeRider
from models.group_model import Group
from models.user_model import User
from models.evaluation_model import Evaluation
from service.github_service import GitHubService
from schemas.free_rider import FreeRiderResponse
from beanie import Link


class TestGetFreeRider:
    
    @pytest.fixture
    def mock_github_service(self):
        """Mock GitHub service"""
        service = Mock(spec=GitHubService)
        service.get_repo_contributors = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_group(self):
        """Sample group data"""
        group = Mock(spec=Group)
        group.id = ObjectId()
        group.name = "Test Group"
        group.github_link = "https://github.com/testuser/testrepo"
        group.members = Mock()
        group.project = Mock()
        return group
    
    @pytest.fixture
    def sample_users(self):
        """Sample user data"""
        users = []
        for i in range(3):
            user = Mock(spec=User)
            user.id = ObjectId()
            user.username = f"user{i}"
            user.github_user = f"github_user{i}"
            users.append(user)
        return users
    
    @pytest.fixture
    def sample_project(self):
        """Sample project data"""
        project = Mock()
        project.id = ObjectId()
        return project
    
    @pytest.fixture
    def sample_contributors(self):
        """Sample GitHub contributors data"""
        return [
            {
                "contributor": "github_user0",
                "commit_count": 50,
                "lines_added": 1000,
                "lines_removed": 200,
                "files_modified": 25,
                "last_commit_date": "2024-01-15T10:30:00",
                "loc": 1200
            },
            {
                "contributor": "github_user1",
                "commit_count": 30,
                "lines_added": 600,
                "lines_removed": 100,
                "files_modified": 15,
                "last_commit_date": "2024-01-14T15:45:00",
                "loc": 700
            },
            {
                "contributor": "github_user2",
                "commit_count": 5,
                "lines_added": 50,
                "lines_removed": 10,
                "files_modified": 3,
                "last_commit_date": "2024-01-10T09:15:00",
                "loc": 60
            }
        ]
    
    @pytest.fixture
    def sample_evaluations(self):
        """Sample evaluation data"""
        evals = []
        for i in range(3):
            for j in range(2):  # 2 evaluations per user
                eval_mock = Mock(spec=Evaluation)
                eval_mock.score = 0.8 if i < 2 else 0.1  # First two users get good scores
                evals.append(eval_mock)
        return evals

    @pytest.mark.asyncio
    async def test_get_free_rider_success(self, mock_github_service, sample_group, sample_users, 
                                        sample_project, sample_contributors, sample_evaluations):
        """Test successful free rider detection"""
        group_id = str(sample_group.id)
        
        # Mock database operations
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id), \
             patch('routes.free_rider_routes.Evaluation.find') as mock_eval_find, \
             patch('routes.free_rider_routes.FreeRider.find') as mock_fr_find:
            
            # Setup mocks
            sample_group.members.fetch = AsyncMock(return_value=sample_users)
            sample_group.project.fetch = AsyncMock(return_value=sample_project)
            mock_github_service.get_repo_contributors.return_value = sample_contributors
            
            # Mock evaluations for each user
            mock_eval_find.return_value.to_list = AsyncMock(return_value=sample_evaluations[:2])  # Good scores for first user
            
            # Mock FreeRider operations
            mock_fr_find.return_value.delete = AsyncMock()
            mock_fr_find.return_value.to_list = AsyncMock(return_value=[])
            
            with patch('routes.free_rider_routes.FreeRider') as mock_fr_class:
                mock_fr_instance = Mock()
                mock_fr_instance.insert = AsyncMock()
                mock_fr_class.return_value = mock_fr_instance
                
                result = await get_free_rider(group_id, mock_github_service)
                
                # Verify GitHub service was called correctly
                mock_github_service.get_repo_contributors.assert_called_once_with("testrepo", "testuser")
                
                # Verify the result
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_free_rider_group_not_found(self, mock_github_service):
        """Test when group is not found"""
        group_id = str(ObjectId())
        
        with patch('routes.free_rider_routes.Group.get', return_value=None), \
             patch('routes.free_rider_routes.ObjectId', return_value=ObjectId(group_id)):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_free_rider(group_id, mock_github_service)
            
            assert exc_info.value.status_code == 404
            assert exc_info.value.detail == "Group not found"

    @pytest.mark.asyncio
    async def test_get_free_rider_no_github_link(self, mock_github_service, sample_group):
        """Test when group has no GitHub link"""
        group_id = str(sample_group.id)
        sample_group.github_link = None
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id):
            
            with pytest.raises(HTTPException) as exc_info:
                await get_free_rider(group_id, mock_github_service)
            
            assert exc_info.value.status_code == 400
            assert exc_info.value.detail == "Group does not have a GitHub link"

    @pytest.mark.asyncio
    async def test_get_free_rider_github_service_error(self, mock_github_service, sample_group, sample_users):
        """Test when GitHub service raises an error"""
        group_id = str(sample_group.id)
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id):
            
            sample_group.members.fetch = AsyncMock(return_value=sample_users)
            mock_github_service.get_repo_contributors.side_effect = Exception("GitHub API Error")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_free_rider(group_id, mock_github_service)
            
            assert exc_info.value.status_code == 400
            assert "GitHub API Error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_free_rider_empty_contributors(self, mock_github_service, sample_group, sample_users, sample_project):
        """Test when there are no contributors from GitHub"""
        group_id = str(sample_group.id)
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id), \
             patch('routes.free_rider_routes.Evaluation.find') as mock_eval_find, \
             patch('routes.free_rider_routes.FreeRider.find') as mock_fr_find:
            
            sample_group.members.fetch = AsyncMock(return_value=sample_users)
            sample_group.project.fetch = AsyncMock(return_value=sample_project)
            mock_github_service.get_repo_contributors.return_value = []
            
            mock_eval_find.return_value.to_list = AsyncMock(return_value=[])
            mock_fr_find.return_value.delete = AsyncMock()
            mock_fr_find.return_value.to_list = AsyncMock(return_value=[])
            
            with patch('routes.free_rider_routes.FreeRider') as mock_fr_class:
                mock_fr_instance = Mock()
                mock_fr_instance.insert = AsyncMock()
                mock_fr_class.return_value = mock_fr_instance
                
                result = await get_free_rider(group_id, mock_github_service)
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_free_rider_score_calculation(self, mock_github_service, sample_group, sample_users, 
                                                  sample_project, sample_contributors):
        """Test score calculation logic"""
        group_id = str(sample_group.id)
        
        # Create mock evaluations with specific scores
        mock_evaluations = [Mock(score=0.9), Mock(score=0.8)]  # Average = 0.85
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id), \
             patch('routes.free_rider_routes.Evaluation.find') as mock_eval_find, \
             patch('routes.free_rider_routes.FreeRider.find') as mock_fr_find:
            
            sample_group.members.fetch = AsyncMock(return_value=[sample_users[0]])  # Only test first user
            sample_group.project.fetch = AsyncMock(return_value=sample_project)
            mock_github_service.get_repo_contributors.return_value = sample_contributors
            
            mock_eval_find.return_value.to_list = AsyncMock(return_value=mock_evaluations)
            mock_fr_find.return_value.delete = AsyncMock()
            mock_fr_find.return_value.to_list = AsyncMock(return_value=[])
            
            with patch('routes.free_rider_routes.FreeRider') as mock_fr_class:
                mock_fr_instance = Mock()
                mock_fr_instance.insert = AsyncMock()
                mock_fr_class.return_value = mock_fr_instance
                
                await get_free_rider(group_id, mock_github_service)
                
                # Verify that FreeRider was not created (score should be high enough)
                # With max_loc=1200, min_loc=60, user0 has loc=1200
                # loc_score = (1200-60)/(1200-60) = 1.0
                # real_score = 1.0 * 0.2 + 0.85 * 0.8 = 0.2 + 0.68 = 0.88
                # This should NOT be a free rider (>= 0.2)
                mock_fr_class.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_free_rider_low_score_creates_freerider(self, mock_github_service, sample_group, 
                                                            sample_users, sample_project, sample_contributors):
        """Test that low score creates a free rider entry"""
        group_id = str(sample_group.id)
        
        # Create mock evaluations with low scores
        mock_evaluations = [Mock(score=0.1), Mock(score=0.1)]  # Average = 0.1
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id), \
             patch('routes.free_rider_routes.Evaluation.find') as mock_eval_find, \
             patch('routes.free_rider_routes.FreeRider.find') as mock_fr_find:
            
            sample_group.members.fetch = AsyncMock(return_value=[sample_users[2]])  # Use user with low contribution
            sample_group.project.fetch = AsyncMock(return_value=sample_project)
            mock_github_service.get_repo_contributors.return_value = sample_contributors
            
            mock_eval_find.return_value.to_list = AsyncMock(return_value=mock_evaluations)
            mock_fr_find.return_value.delete = AsyncMock()
            mock_fr_find.return_value.to_list = AsyncMock(return_value=[])
            
            with patch('routes.free_rider_routes.FreeRider') as mock_fr_class:
                mock_fr_instance = Mock()
                mock_fr_instance.insert = AsyncMock()
                mock_fr_class.return_value = mock_fr_instance
                
                await get_free_rider(group_id, mock_github_service)
                
                # With min_loc=60, max_loc=1200, user2 has loc=60
                # loc_score = (60-60)/(1200-60) = 0
                # real_score = 0 * 0.2 + 0.1 * 0.8 = 0.08
                # This should be a free rider (< 0.2)
                mock_fr_class.assert_called_once()
                mock_fr_instance.insert.assert_called_once()

    def test_get_github_service(self):
        """Test the dependency injection function"""
        service = get_github_service()
        assert isinstance(service, GitHubService)

    @pytest.mark.asyncio
    async def test_get_free_rider_invalid_object_id(self, mock_github_service):
        """Test with invalid ObjectId"""
        with patch('routes.free_rider_routes.ObjectId', side_effect=Exception("Invalid ObjectId")):
            with pytest.raises(HTTPException) as exc_info:
                await get_free_rider("invalid_id", mock_github_service)
            
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_free_rider_no_members(self, mock_github_service, sample_group):
        """Test when group has no members"""
        group_id = str(sample_group.id)
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id), \
             patch('routes.free_rider_routes.FreeRider.find') as mock_fr_find:
            
            sample_group.members.fetch = AsyncMock(return_value=[])
            mock_github_service.get_repo_contributors.return_value = []
            mock_fr_find.return_value.to_list = AsyncMock(return_value=[])
            
            result = await get_free_rider(group_id, mock_github_service)
            assert result == []

    @pytest.mark.asyncio
    async def test_free_rider_response_formatting(self, mock_github_service, sample_group, 
                                                sample_users, sample_project):
        """Test that FreeRiderResponse is properly formatted"""
        group_id = str(sample_group.id)
        
        # Create a mock free rider
        mock_free_rider = Mock()
        mock_free_rider.score = 0.15
        mock_free_rider.commit_count = 5
        mock_free_rider.lines_added = 50
        mock_free_rider.lines_removed = 10
        mock_free_rider.files_modified = 3
        mock_free_rider.last_commit_date = datetime(2024, 1, 10, 9, 15, 0)
        mock_free_rider.user = Mock()
        mock_free_rider.user.fetch = AsyncMock(return_value=sample_users[0])
        mock_free_rider.group = Mock()
        mock_free_rider.group.fetch = AsyncMock(return_value=sample_group)
        
        with patch('routes.free_rider_routes.Group.get', return_value=sample_group), \
             patch('routes.free_rider_routes.ObjectId', return_value=sample_group.id), \
             patch('routes.free_rider_routes.FreeRider.find') as mock_fr_find:
            
            sample_group.members.fetch = AsyncMock(return_value=[])
            mock_github_service.get_repo_contributors.return_value = []
            mock_fr_find.return_value.to_list = AsyncMock(return_value=[mock_free_rider])
            
            result = await get_free_rider(group_id, mock_github_service)
            
            assert len(result) == 1
            assert result[0].score == 0.15
            assert result[0].commit_count == 5
            assert result[0].lines_added == 50
            assert result[0].lines_removed == 10
            assert result[0].files_modified == 3
            assert result[0].last_commit_date == "2024-01-10T09:15:00"