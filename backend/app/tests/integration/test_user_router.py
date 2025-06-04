import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(test_app: AsyncClient):
    """Test đăng ký user mới thành công"""
    payload = {
        "HoDem": "Nguyen Van",
        "Ten": "A",
        "email": "nguyenvana@example.com",
        "password": "abc123",
        "role": "student",
        "github_user": "nguyenvana"  # Thêm field bắt buộc
    }

    res = await test_app.post("/users/register", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == payload["email"]
    assert data["ho_ten"] == "Nguyen Van A"
    assert data["role"] == "student"

@pytest.mark.asyncio
async def test_register_duplicate_email(test_app: AsyncClient):
    """Test đăng ký với email đã tồn tại"""
    # Đăng ký user đầu tiên
    payload = {
        "HoDem": "Nguyen Van",
        "Ten": "B",
        "email": "duplicate@example.com",
        "password": "abc123",
        "role": "student",
        "github_user": "nguyenvanb"
    }
    
    # Đăng ký lần đầu - thành công
    res1 = await test_app.post("/users/register", json=payload)
    assert res1.status_code == 200
    
    # Đăng ký lần hai với cùng email - thất bại
    res2 = await test_app.post("/users/register", json=payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_user_success(test_app: AsyncClient):
    """Test đăng nhập thành công"""
    # Đăng ký user trước
    register_payload = {
        "HoDem": "Test",
        "Ten": "Login",
        "email": "testlogin@example.com",
        "password": "testpass123",
        "role": "student",
        "github_user": "testlogin"
    }
    await test_app.post("/users/register", json=register_payload)
    
    # Đăng nhập
    form_data = {
        "username": "testlogin@example.com",  # OAuth2PasswordRequestForm sử dụng username
        "password": "testpass123"
    }

    res = await test_app.post("/users/login", data=form_data)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_user_invalid_credentials(test_app: AsyncClient):
    """Test đăng nhập với thông tin sai"""
    form_data = {
        "username": "nonexistent@example.com",
        "password": "wrongpassword"
    }

    res = await test_app.post("/users/login", data=form_data)
    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_get_current_user(test_app: AsyncClient):
    """Test lấy thông tin user hiện tại"""
    # Đăng ký user
    register_payload = {
        "HoDem": "Current",
        "Ten": "User",
        "email": "currentuser@example.com",
        "password": "currentpass123",
        "role": "student",
        "github_user": "currentuser"
    }
    await test_app.post("/users/register", json=register_payload)
    
    # Đăng nhập để lấy token
    login_data = {
        "username": "currentuser@example.com",
        "password": "currentpass123"
    }
    login_res = await test_app.post("/users/login", data=login_data)
    token = login_res.json()["access_token"]

    # Gọi API với token
    headers = {"Authorization": f"Bearer {token}"}
    res = await test_app.get("/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "currentuser@example.com"
    assert data["ho_ten"] == "Current User"

@pytest.mark.asyncio
async def test_get_current_user_unauthorized(test_app: AsyncClient):
    """Test gọi API mà không có token"""
    res = await test_app.get("/users/me")
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_search_user_found(test_app: AsyncClient):
    """Test tìm kiếm user thành công"""
    # Đăng ký user để tìm kiếm
    register_payload = {
        "HoDem": "Search",
        "Ten": "Test",
        "email": "searchtest@example.com",
        "password": "searchpass123",
        "role": "student",
        "github_user": "searchtest"
    }
    await test_app.post("/users/register", json=register_payload)
    
    # Tìm kiếm theo email
    res = await test_app.get("/users/search?search=searchtest@example.com")
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "searchtest@example.com"
    assert data["ho_ten"] == "Search Test"
    assert "role" in data

@pytest.mark.asyncio
async def test_search_user_by_name(test_app: AsyncClient):
    """Test tìm kiếm user theo tên"""
    # Đăng ký user
    register_payload = {
        "HoDem": "Name",
        "Ten": "Search",
        "email": "namesearch@example.com",
        "password": "namepass123",
        "role": "student",
        "github_user": "namesearch"
    }
    await test_app.post("/users/register", json=register_payload)
    
    # Tìm kiếm theo tên
    res = await test_app.get("/users/search?search=Name Search")
    assert res.status_code == 200
    data = res.json()
    assert data["ho_ten"] == "Name Search"
    assert data["email"] == "namesearch@example.com"

@pytest.mark.asyncio
async def test_search_user_not_found(test_app: AsyncClient):
    """Test tìm kiếm user không tồn tại"""
    res = await test_app.get("/users/search?search=nonexistentuser")
    # API trả về None nếu không tìm thấy, cần xử lý lỗi 404 hoặc kiểm tra response
    assert res.status_code in [200, 404]  # Tùy thuộc vào cách API xử lý

@pytest.mark.asyncio
async def test_get_all_users_authenticated(test_app: AsyncClient):
    """Test lấy danh sách tất cả users (cần authentication)"""
    # Đăng ký admin user
    admin_payload = {
        "HoDem": "Admin",
        "Ten": "User",
        "email": "admin@example.com",
        "password": "adminpass123",
        "role": "admin",
        "github_user": "adminuser"
    }
    await test_app.post("/users/register", json=admin_payload)
    
    # Đăng nhập admin
    login_data = {
        "username": "admin@example.com",
        "password": "adminpass123"
    }
    login_res = await test_app.post("/users/login", data=login_data)
    token = login_res.json()["access_token"]
    
    # Gọi API get all users
    headers = {"Authorization": f"Bearer {token}"}
    res = await test_app.get("/users/get-all", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_students_by_group(test_app: AsyncClient):
    """Test lấy danh sách sinh viên theo nhóm"""
    group_id = "test_group_123"
    res = await test_app.get(f"/users/students-by-group/{group_id}")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_students_by_project(test_app: AsyncClient):
    """Test lấy danh sách sinh viên theo dự án"""
    project_id = "test_project_123"
    res = await test_app.get(f"/users/students-by-project/{project_id}")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)