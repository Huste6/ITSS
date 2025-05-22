from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.task_model import Task
from models.group_model import Group
from models.user_model import User
from models.project_model import Project
from schemas.task_schemas import TaskCreate, TaskResponse
from schemas.pyobjectid_schemas import PyObjectId
from routes.user_routes import get_current_user
from beanie import Link
import asyncio
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}} 
)

@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate, 
                      current_user: User = Depends(get_current_user),
                      description: str = "Create a new task. Only mentors can create tasks.",
                      summary: str = "Create a new task"):
    try:
        group = await Group.get(task.group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        
        project = await group.project.fetch()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate and get assigned students
        assigned_students = []
        for student_id in task.assigned_student_ids:
            student = await User.get(PyObjectId(student_id))
            if not student or student.role != "student":
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
            assigned_students.append(Link(student, document_class=User))

        # Create new task
        new_task = Task(
            title=task.title,
            description=task.description,
            group=Link(group, document_class=Group),
            assigned_students=assigned_students,
            status=task.status,
            deadline=task.deadline,
            related_to_project=Link(project, document_class=Project),
            priority=task.priority or "Medium"
        )
        await new_task.save()

        # Add task to group
        group.allTasks = await group.fetch_link("allTasks") or []
        group.allTasks.append(Link(new_task, document_class=Task))
        await group.save()
        
        # Prepare response data
        students_data = []
        for student_link in new_task.assigned_students:
            student = await student_link.fetch() if isinstance(student_link, Link) else student_link
            students_data.append({
                "id": str(student.id),
                "name": student.ho_ten,
                "email": student.email
            })

        logger.info(f"Created new task: {new_task.id}")
        
        return TaskResponse(
            _id=new_task.id,
            id=str(new_task.id),
            title=new_task.title,
            description=new_task.description,
            group_id=str(group.id),
            group_name=group.name,
            assigned_students=students_data,
            status=new_task.status,
            deadline=new_task.deadline,
            priority=new_task.priority
        )
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.get("/", response_model=list[TaskResponse],
            description="Get all tasks. Only mentors can view tasks.",
            summary="Get all tasks")
async def get_all_tasks(current_user: User = Depends(get_current_user),
                        skip: int = Query(0, ge=0, description="Number of tasks to skip"),
                        limit: int = Query(50, ge=1, le=100, description="Maximum number of tasks to return")):
    try:
        tasks = await Task.find_all().skip(skip).limit(limit).to_list()
        result = []
        for task in tasks:
           group = await task.group.fetch() if isinstance(task.group, Link) else task.group
           assigned_students = []
           for student_link in task.assigned_students:
                student = await student_link.fetch() if isinstance(student_link, Link) else student_link
                assigned_students.append({
                    "id": str(student.id),
                    "ho_ten": student.ho_ten,
                    "email": student.email
         })
           result.append(TaskResponse(
               _id=task.id,
                id=str(task.id),
               title=task.title,
               description=task.description,
               group_id=str(group.id),
               group_name=group.name,
               assigned_students=assigned_students,
               status=task.status,
               deadline=task.deadline,
               priority=task.priority
           ))
        return result
    except Exception as e:
       logger.error(f"Error fetching all tasks: {str(e)}")
       raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{task_id}", response_model=TaskResponse,
            description="Get a task by ID. Only mentors can view tasks.",
            summary="Get a task by ID")
async def get_task(task_id: str, current_user: User = Depends(get_current_user)):
    try:
        task_id_obj = PyObjectId.validate(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    try:
        task = await Task.get(task_id_obj)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        group = await task.group.fetch() if isinstance(task.group, Link) else task.group
        assigned_students = []
        for student_link in task.assigned_students:
            student = await student_link.fetch() if isinstance(student_link, Link) else student_link
            assigned_students.append({
                "id": str(student.id),
                "name": student.ho_ten,
                "email": student.email
            })
              

        logger.info(f"Task found: {task.id}")

        return TaskResponse(
            _id=task.id,
            title=task.title,
            description=task.description,
            group_id=str(group.id),
            group_name=group.name,
            assigned_students=assigned_students,
            status=task.status,
            deadline=task.deadline,
            priority=task.priority
        )
    except Exception as e:
        logger.error(f"Error getting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{task_id}", response_model=TaskResponse,
            description="Update a task by ID. Only mentors can update tasks.",
            summary="Update a task by ID")
async def update_task(task_id: str, task: TaskCreate, current_user: User = Depends(get_current_user)):
    try:
        # Lấy task từ database
        db_task = await Task.get(task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Lấy group liên quan
        group = await Group.get(task.group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Lấy project liên quan
        project = await group.project.fetch()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Lấy danh sách students cũ
        old_students = []
        if db_task.assigned_students:
            for student_ref in db_task.assigned_students:
                if isinstance(student_ref, Link):
                    student = await student_ref.fetch()
                else:
                    student = student_ref
                old_students.append(student)

        # Thêm task vào sinh viên mới
        assigned_students = []
        for student_id in task.assigned_student_ids:
            student = await User.get(student_id)
            if not student or student.role != "student":
                raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
            assigned_students.append(Link(student, document_class=User))

        # Cập nhật task
        db_task.title = task.title
        db_task.description = task.description
        db_task.group = Link(group, document_class=Group)
        db_task.assigned_students = assigned_students
        db_task.status = task.status
        db_task.deadline = task.deadline
        db_task.related_to_project = Link(project, document_class=Project)
        db_task.priority = task.priority
        await db_task.save()

        # Chuyển đổi dữ liệu để trả về
        students_data = []
        for student_ref in db_task.assigned_students:
            if isinstance(student_ref, Link):
                student = await student_ref.fetch()
            else:
                student = student_ref
            students_data.append({
                "id": str(student.id),
                "name": student.ho_ten,
                "email": student.email
            })

        logger.info(f"Updated task: {db_task.id}")
        
        return TaskResponse(
            _id=db_task.id,
            id=str(db_task.id),
            title=db_task.title,
            description=db_task.description,
            group_id=str(group.id),
            group_name=group.name,
            assigned_students=students_data,
            status=db_task.status,
            deadline=db_task.deadline,
            priority=db_task.priority
        )
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{task_id}", response_model=dict,
               description="Delete a task by ID. Only mentors can delete tasks.",
               summary="Delete a task by ID")
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    try:
        task = await Task.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Fetch group if task.group is a Link, otherwise use it directly
        group = None
        if isinstance(task.group, Link):
            group = await task.group.fetch()
        elif isinstance(task.group, Group):
            group = task.group
        else:
            raise HTTPException(status_code=404, detail="Group associated with task not found")

        

        # Remove task from group
        group.allTasks = await group.fetch_link("allTasks") or []
        group.allTasks = [t for t in group.allTasks if str(t.ref.id) != task_id]
        await group.save()

        # Delete the task
        await task.delete()
        
        logger.info(f"Deleted task: {task_id}")
        
        return {"message": "Task deleted"}
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")