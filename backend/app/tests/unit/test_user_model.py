import pytest
from pydantic import ValidationError
from models.user_model import User
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from models.group_model import Group
from models.task_model import Task
import asyncio

def test_valid_user_creation():
    user = User(
        HoDem="Nguyen Van",
        Ten="A",
        email="a@example.com",
        password="abc123",
        role="admin",
        group_id=None,
        tasks=[],
        contributions="10",
        ho_ten="Nguyen Van A"
    )
    assert user.email == "a@example.com"
    assert user.ho_ten == "Nguyen Van A"
    assert user.role == "admin"
    assert user.tasks == []

def test_missing_required_fields():
    with pytest.raises(ValidationError):
        User(
            email="a@example.com",
            password="abc123",
            role="mentor"
            # thiếu HoDem và Ten
        )

def test_invalid_email_format():
    with pytest.raises(ValidationError):
        User(
            HoDem="Le",
            Ten="B",
            email="invalid-email",
            password="pass",
            role="mentor"
        )

def test_optional_fields_can_be_none():
    user = User(
        HoDem="Tran",
        Ten="C",
        email="c@example.com",
        password="123",
        role="mentor",
        group_id=None,
        tasks=None,
        contributions=None
    )
    assert user.group_id is None
    assert user.tasks is None
    assert user.contributions is None