import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_get_user_github_success(test_app: AsyncClient):
    """Test lấy thông tin GitHub user thành công"""
    username = "testuser"
    mock_user_info = {
        "login": "testuser",
        "name": "Test User",
        "avatar_url": "https://avatars.githubusercontent.com/u/123456",
        "public_repos": 10,
        "followers": 5,
        "following": 3,
        "created_at": "2020-01-01T00:00:00Z"
    }
    
    with patch('service.github_service.GitHubService.get_user_info', return_value=mock_user_info):
        res = await test_app.get(f"/github/user_github?username={username}")
        assert res.status_code == 200
        data = res.json()
        assert data["login"] == "testuser"
        assert data["name"] == "Test User"
        assert data["public_repos"] == 10

@pytest.mark.asyncio
async def test_get_user_github_not_found(test_app: AsyncClient):
    """Test lấy thông tin GitHub user không tồn tại"""
    username = "nonexistentuser"
    
    with patch('service.github_service.GitHubService.get_user_info', side_effect=Exception("User not found")):
        res = await test_app.get(f"/github/user_github?username={username}")
        assert res.status_code == 400
        assert "User not found" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_repositories_success(test_app: AsyncClient):
    """Test lấy danh sách repositories của user thành công"""
    username = "testuser"
    mock_repos = [
        {
            "name": "repo1",
            "description": "Test repository 1",
            "html_url": "https://github.com/testuser/repo1",
            "language": "Python",
            "stargazers_count": 5,
            "forks_count": 2
        },
        {
            "name": "repo2",
            "description": "Test repository 2",
            "html_url": "https://github.com/testuser/repo2",
            "language": "JavaScript",
            "stargazers_count": 3,
            "forks_count": 1
        }
    ]
    
    with patch('service.github_service.GitHubService.get_user_repositories', return_value=mock_repos):
        res = await test_app.get(f"/github/repos?username={username}")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["name"] == "repo1"
        assert data[1]["name"] == "repo2"

@pytest.mark.asyncio
async def test_get_repo_commits_success(test_app: AsyncClient):
    """Test lấy danh sách commits của repository thành công"""
    username = "testuser"
    repo_name = "testrepo"
    mock_commits = [
        {
            "sha": "abc123",
            "commit": {
                "message": "Initial commit",
                "author": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "date": "2024-01-01T00:00:00Z"
                }
            },
            "author": {
                "login": "testuser"
            }
        }
    ]
    
    with patch('service.github_service.GitHubService.get_repo_commits', return_value=mock_commits):
        res = await test_app.get(f"/github/repos?username={username}&repo_name={repo_name}&type=commits")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["sha"] == "abc123"
        assert data[0]["commit"]["message"] == "Initial commit"

@pytest.mark.asyncio
async def test_get_repo_commits_missing_repo_name(test_app: AsyncClient):
    """Test lấy commits mà không có repo_name"""
    username = "testuser"
    
    res = await test_app.get(f"/github/repos?username={username}&type=commits")
    assert res.status_code == 400
    assert "Missing repo_name for the requested type" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_repo_contributors_success(test_app: AsyncClient):
    """Test lấy danh sách contributors của repository thành công"""
    username = "testuser"
    repo_name = "testrepo"
    mock_contributors = [
        {
            "login": "contributor1",
            "contributions": 25,
            "avatar_url": "https://avatars.githubusercontent.com/u/111111"
        },
        {
            "login": "contributor2",
            "contributions": 15,
            "avatar_url": "https://avatars.githubusercontent.com/u/222222"
        }
    ]
    
    with patch('service.github_service.GitHubService.get_repo_contributors', return_value=mock_contributors):
        res = await test_app.get(f"/github/repos?username={username}&repo_name={repo_name}&type=contributors")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["login"] == "contributor1"
        assert data[0]["contributions"] == 25

@pytest.mark.asyncio
async def test_get_repo_contributors_missing_repo_name(test_app: AsyncClient):
    """Test lấy contributors mà không có repo_name"""
    username = "testuser"
    
    res = await test_app.get(f"/github/repos?username={username}&type=contributors")
    assert res.status_code == 400
    assert "Missing repo_name for the requested type" in res.json()["detail"]

@pytest.mark.asyncio
async def test_analyze_contributor_activity_success(test_app: AsyncClient):
    """Test phân tích hoạt động contributor thành công"""
    username = "testuser"
    repo_name = "testrepo"
    mock_analysis = {
        "total_contributors": 3,
        "active_contributors": 2,
        "potential_free_riders": 1,
        "contributors": [
            {
                "login": "active_user",
                "contributions": 50,
                "activity_score": 85,
                "is_active": True
            },
            {
                "login": "inactive_user",
                "contributions": 2,
                "activity_score": 15,
                "is_active": False
            }
        ]
    }
    
    with patch('service.github_service.GitHubService.analyze_contributor_activity', return_value=mock_analysis):
        res = await test_app.get(f"/github/repos?username={username}&repo_name={repo_name}&type=analysis")
        assert res.status_code == 200
        data = res.json()
        assert data["total_contributors"] == 3
        assert data["active_contributors"] == 2
        assert data["potential_free_riders"] == 1

@pytest.mark.asyncio
async def test_analyze_contributor_activity_missing_repo_name(test_app: AsyncClient):
    """Test phân tích contributor mà không có repo_name"""
    username = "testuser"
    
    res = await test_app.get(f"/github/repos?username={username}&type=analysis")
    assert res.status_code == 400
    assert "Missing repo_name for the requested type" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_repo_invalid_type(test_app: AsyncClient):
    """Test gọi API với type không hợp lệ"""
    username = "testuser"
    repo_name = "testrepo"
    
    res = await test_app.get(f"/github/repos?username={username}&repo_name={repo_name}&type=invalid_type")
    assert res.status_code == 400
    assert "Invalid type" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_free_rider_success(test_app: AsyncClient):
    """Test lấy thông tin free rider thành công"""
    username = "testuser"
    repo_name = "testrepo"
    mock_analysis = {
        "total_contributors": 5,
        "active_contributors": 3,
        "potential_free_riders": 2,
        "contributors": [
            {
                "login": "hard_worker",
                "contributions": 100,
                "activity_score": 95,
                "is_active": True
            },
            {
                "login": "free_rider",
                "contributions": 1,
                "activity_score": 5,
                "is_active": False
            }
        ]
    }
    
    with patch('service.github_service.GitHubService.analyze_contributor_activity', return_value=mock_analysis):
        res = await test_app.get(f"/github/get_free_rider?username={username}&repo_name={repo_name}")
        assert res.status_code == 200
        data = res.json()
        assert data["potential_free_riders"] == 2
        assert len(data["contributors"]) == 2

@pytest.mark.asyncio
async def test_get_free_rider_error(test_app: AsyncClient):
    """Test lấy thông tin free rider gặp lỗi"""
    username = "testuser"
    repo_name = "nonexistentrepo"
    
    with patch('service.github_service.GitHubService.analyze_contributor_activity', side_effect=Exception("Repository not found")):
        res = await test_app.get(f"/github/get_free_rider?username={username}&repo_name={repo_name}")
        assert res.status_code == 400
        assert "Repository not found" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_repo_with_service_error(test_app: AsyncClient):
    """Test gọi API khi service gặp lỗi"""
    username = "testuser"
    
    with patch('service.github_service.GitHubService.get_user_repositories', side_effect=Exception("GitHub API rate limit exceeded")):
        res = await test_app.get(f"/github/repos?username={username}")
        assert res.status_code == 400
        assert "GitHub API rate limit exceeded" in res.json()["detail"]

@pytest.mark.asyncio
async def test_get_user_github_missing_username(test_app: AsyncClient):
    """Test gọi API mà không có username"""
    res = await test_app.get("/github/user_github")
    assert res.status_code == 422  # FastAPI validation error

@pytest.mark.asyncio
async def test_get_repo_missing_username(test_app: AsyncClient):
    """Test gọi API repos mà không có username"""
    res = await test_app.get("/github/repos")
    assert res.status_code == 422  # FastAPI validation error

@pytest.mark.asyncio
async def test_get_free_rider_missing_parameters(test_app: AsyncClient):
    """Test gọi API free rider mà thiếu parameters"""
    # Thiếu cả username và repo_name
    res = await test_app.get("/github/get_free_rider")
    assert res.status_code == 422
    
    # Chỉ có username, thiếu repo_name
    res = await test_app.get("/github/get_free_rider?username=testuser")
    assert res.status_code == 422
    
    # Chỉ có repo_name, thiếu username
    res = await test_app.get("/github/get_free_rider?repo_name=testrepo")
    assert res.status_code == 422