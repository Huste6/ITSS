from datetime import timedelta
from typing import Optional
from bson import Regex
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from models.user_model import User
from outh2 import get_current_user, get_password_hash, verify_password
from token_handler import create_access_token
from schemas.user_schemas import UserCreate, Token, UserResponse
from config import env

# Create router
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Check if user is admin
async def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin privileges required",
        )
    return current_user

# Check if user is mentor
async def get_current_mentor(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["mentor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Mentor privileges required",
        )
    return current_user

# Routes
@router.post("/register")
async def register_user(user: UserCreate):
    existing_user = await User.find_one({"email": user.email})
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create new user
    # hashed_password = get_password_hash(user.password)
    full_name = f"{user.HoDem} {user.Ten}"
    new_user = User(
        HoDem=user.HoDem,
        Ten=user.Ten,
        email=user.email,
        ho_ten=full_name,
        github_user=user.github_user,
        password=user.password,
        role=user.role,
        group_id=None,
        tasks=None,
        contributions=None
    )
    await new_user.insert()
    return new_user

@router.post('/login', response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.email == form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=env.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email, "user_id": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
@router.get('/get-all')
async def get_all_users(current_user: User = Depends(get_current_user)):
    users = await User.find({"role": "student"}).to_list()

    return [
        {
            "id": str(user.id),
            "ho_ten": user.ho_ten,
            "email": user.email,
            "role": user.role,
            "group_id": user.group_id,
        }
        for user in users
    ]
@router.get('/me')
async def get_datail_user(current_user: User = Depends(get_current_user)):
    return current_user

@router.get('/search')
async def search_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
):
    query = {}
    if search:
        query = {
            "$or": [
                {"email": {"$regex": search, "$options": "i"}},
                {"ho_ten": {"$regex": search, "$options": "i"}}
            ]
        }
    
    user = await User.find_one(query)
    return {
        "ho_ten": user.ho_ten,
        "email": user.email,
        "role": user.role
    }

#tìm kiếm sinh viên theo nhóm
@router.get('/students-by-group/{group_id}')
async def get_students_by_group(group_id: str = Path(..., description="Group ID")):
    students = await User.find({
        "role": "student",
        "group_id": group_id
    }).to_list()
    return [
        {
            "ho_ten": student.ho_ten,
            "email": student.email,
            "role": student.role
        }
        for student in students
    ]

#tìm kiếm sinh viên theo dự án
@router.get('/students-by-project/{project_id}')
async def get_students_by_project(project_id: str = Path(..., description="Project ID")):
    students = await User.find(
        {"role": "student",
        "project_id": project_id}
    ).to_list()
    return [
        {
            "ho_ten": student.ho_ten,
            "email": student.email,
            "role": student.role
        }
        for student in students
    ]
    