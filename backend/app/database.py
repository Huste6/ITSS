from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from config import env
from models.user_model import User
from models.task_model import Task
from models.project_model import Project
from models.group_model import Group
from models.evaluation_model import Evaluation
from models.report_model import Report
from pymongo.errors import OperationFailure
import logging

async def init_db(test: bool = False):
    try:
        mongo_uri = f"{env.MONGO_URI}?authSource=admin"
        client = AsyncIOMotorClient(mongo_uri)
        db_name = "test_db" if test else env.DATABASE_NAME
        db = client[db_name]

        await init_beanie(
            database=db,
            document_models=[User, Task, Project, Group, Evaluation, Report]
        )
        logging.info(f"Connected to MongoDB: {db_name}")
    except OperationFailure as e:
        logging.error("Connect fail: %s", e)