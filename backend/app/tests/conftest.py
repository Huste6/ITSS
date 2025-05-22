import pytest
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from main import app_instance
from models.user_model import User
from models.group_model import Group
from models.task_model import Task

@pytest.fixture(scope="session", autouse=True)
async def test_db():    
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_db"]
    
    await init_beanie(database=db, document_models=[User, Group, Task])
    
    await User.delete_all()
    await Group.delete_all()
    await Task.delete_all()

    yield
    
    await client.drop_database("test_db")

@pytest.fixture(scope="module")
async def test_app():
    async with AsyncClient(app=app_instance, base_url="http://test") as ac:
        yield ac
