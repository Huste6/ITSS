import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(test_app: AsyncClient):
    payload = {
        "HoDem": "Nguyen Van",
        "Ten": "A",
        "email": "nguyenvana@example.com",
        "password": "abc123",
        "role": "student"
    }

    res = await test_app.post("/users/register", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == payload["email"]
    assert data["ho_ten"] == "Nguyen Van A"

@pytest.mark.asyncio
async def test_register_duplicate_email(test_app: AsyncClient):
    payload = {
        "HoDem": "Nguyen Van",
        "Ten": "A",
        "email": "nguyenvana@example.com",
        "password": "abc123",
        "role": "student"
    }

    res = await test_app.post("/users/register", json=payload)
    assert res.status_code == 400
    assert res.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_user(test_app: AsyncClient):
    form_data = {
        "username": "nguyenvana@example.com",
        "password": "abc123"  # Giả định là đúng vì chưa hash
    }

    res = await test_app.post("/users/login", data=form_data)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_get_current_user(test_app: AsyncClient):
    # Login để lấy token
    res = await test_app.post("/users/login", data={
        "username": "nguyenvana@example.com",
        "password": "abc123"
    })
    token = res.json()["access_token"]

    # Gọi API cần xác thực
    headers = {"Authorization": f"Bearer {token}"}
    res = await test_app.get("/users/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "nguyenvana@example.com"

@pytest.mark.asyncio
async def test_search_user(test_app: AsyncClient):
    res = await test_app.get("/users/search?search=nguyen")
    assert res.status_code == 200
    data = res.json()
    assert "email" in data
