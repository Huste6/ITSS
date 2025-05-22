from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class GroupCreate(BaseModel):
    name: str
    project_id: str
    leader_id: str 

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class GroupResponse(BaseModel):
    _id: str
    name: str
    project_id: str
    project_title: str
    project_description: Optional[str] = None
    leader_id: str
    leader_name: str
    leader_email: str
    member_ids: Optional[List[str]]
    member_names: Optional[List[str]]
    member_emails: Optional[List[str]]
    

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

