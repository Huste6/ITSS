from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.evaluation_model import Evaluation
from models.user_model import User
from models.project_model import Project
from schemas.evaluation_schemas import EvaluationCreate, EvaluationResponse
from schemas.pyobjectid_schemas import PyObjectId
from routes.user_routes import get_current_user
from beanie import Link
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    prefix="/evaluations",
    tags=["evaluations"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=EvaluationResponse,
               description="Create a new evaluation. Only students can create evaluations.",
               summary="Create a new evaluation")
async def create_evaluation(evaluation: EvaluationCreate, current_user: User = Depends(get_current_user)):
    try:
        # Validate and get student
        student_id = PyObjectId.validate(evaluation.student_id)
        student = await User.get(student_id)
        

        # Validate and get project
        project_id = PyObjectId.validate(evaluation.project_id)
        project = await Project.get(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Create new evaluation
        new_evaluation = Evaluation(
            evaluator=Link(current_user, document_class=User),
            student=Link(student, document_class=User),
            project=Link(project, document_class=Project),
            score=evaluation.score,
            comment=evaluation.comment,
        )
        await new_evaluation.insert()
        logger.info(f"Created new evaluation: {new_evaluation.id}")

        # Return response without fetching again
        return EvaluationResponse(
            id=new_evaluation.id,
            evaluator={"id": str(current_user.id), "ho_ten": current_user.ho_ten, "email": current_user.email},
            student={"id": str(student.id), "ho_ten": student.ho_ten, "email": student.email},
            project={"id": str(project.id), "title": project.title, "description": project.description},
            score=new_evaluation.score,
            comment=new_evaluation.comment
        )
    except Exception as e:
        logger.error(f"Error creating evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=list[EvaluationResponse],
            description="Get all evaluations. Only the evaluator can view their evaluations.",
            summary="Get all evaluations")
async def get_all_evaluations(current_user: User = Depends(get_current_user),
                              skip: int=Query(0, ge=0, description="Number of reports to skip"), 
                              limit: int=Query(10, le=100, description="Maximum number of reports to return")):
    try:
        # Lấy tất cả evaluations
        evaluations = await Evaluation.find().skip(skip).limit(limit).to_list()
        result = []
        for evaluation in evaluations:
            # Fetch evaluator, student, project
            evaluator = await evaluation.evaluator.fetch() if isinstance(evaluation.evaluator, Link) else evaluation.evaluator
            if not evaluator:
                logger.error(f"Failed to resolve evaluator for evaluation {evaluation.id}")
                continue

            student = await evaluation.student.fetch() if isinstance(evaluation.student, Link) else evaluation.student
            if not student:
                logger.error(f"Failed to resolve student for evaluation {evaluation.id}")
                continue

            project = await evaluation.project.fetch() if isinstance(evaluation.project, Link) else evaluation.project
            if not project:
                logger.error(f"Failed to resolve project for evaluation {evaluation.id}")
                continue

            # Kiểm tra quyền truy cập: chỉ trả về evaluation của current_user
            if str(evaluator.id) != str(current_user.id):
                continue

            result.append(EvaluationResponse(
                _id=evaluation.id,
                evaluator={"id": str(current_user.id), "ho_ten": current_user.ho_ten, "email": current_user.email},
                student={"id": str(student.id), "ho_ten": student.ho_ten, "email": student.email},
                project={"id": str(project.id), "title": project.title, "description": project.description},
                score=evaluation.score,
                comment=evaluation.comment
            ))
        return result
    except Exception as e:
        logger.error(f"Error fetching all evaluations: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{evaluation_id}", response_model=EvaluationResponse,
            description="Get an evaluation by ID. Only the evaluator can view their evaluation.",
            summary="Get an evaluation by ID")
async def get_evaluation(evaluation_id: str, current_user: User = Depends(get_current_user)):
    # Validate and get evaluation
    try:
        evaluation_id_obj = PyObjectId.validate(evaluation_id)
        evaluation = await Evaluation.get(evaluation_id_obj)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation_id format")
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    try:
        evaluator = await evaluation.evaluator.fetch() if isinstance(evaluation.evaluator, Link) else evaluation.evaluator
        student = await evaluation.student.fetch() if isinstance(evaluation.student, Link) else evaluation.student
        project = await evaluation.project.fetch() if isinstance(evaluation.project, Link) else evaluation.project

        return EvaluationResponse(
            _id=str(evaluation.id),
            evaluator={"id": str(current_user.id), "ho_ten": current_user.ho_ten, "email": current_user.email},
            student={"id": str(student.id), "ho_ten": student.ho_ten, "email": student.email},
            project={"id": str(project.id), "title": project.title, "description": project.description},
            score=evaluation.score,
            comment=evaluation.comment
        )
    except Exception as e:
        logger.error(f"Error fetching evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{evaluation_id}", response_model=EvaluationResponse,
            description="Update an evaluation. Only the evaluator can update their evaluation.",
            summary="Update an evaluation")
async def update_evaluation(evaluation_id: str, evaluation: EvaluationCreate, current_user: User = Depends(get_current_user)):
    # Validate and get evaluation
    try:
        evaluation_id_obj = PyObjectId.validate(evaluation_id)
        db_evaluation = await Evaluation.get(evaluation_id_obj)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation_id format")
    if not db_evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check evaluator (handle both Link and User)
    evaluator_id = None
    if isinstance(db_evaluation.evaluator, Link):
        evaluator_id = db_evaluation.evaluator.ref.id if db_evaluation.evaluator.ref else None
    elif isinstance(db_evaluation.evaluator, User):
        evaluator_id = db_evaluation.evaluator.id

    if not evaluator_id:
        logger.error(f"Invalid evaluator reference for evaluation {db_evaluation.id}")
        raise HTTPException(status_code=404, detail="Evaluator associated with evaluation not found")

    # Fetch evaluator only if it is a Link
    evaluator = db_evaluation.evaluator if isinstance(db_evaluation.evaluator, User) else await db_evaluation.evaluator.fetch()
    if not evaluator:
        logger.error(f"Failed to resolve evaluator for evaluation {db_evaluation.id}")
        raise HTTPException(status_code=404, detail="Evaluator associated with evaluation not found")

    

    # Validate and get student
    try:
        student_id = PyObjectId.validate(evaluation.student_id)
        student = await User.get(student_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid student_id format")
    

    # Validate and get project
    try:
        project_id = PyObjectId.validate(evaluation.project_id)
        project = await Project.get(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id format")
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


    # Update evaluation
    db_evaluation.student = Link(student, document_class=User)
    db_evaluation.project = Link(project, document_class=Project)
    db_evaluation.score = evaluation.score
    db_evaluation.comment = evaluation.comment
    await db_evaluation.save()
    logger.info(f"Updated evaluation: {db_evaluation.id}")

    # Return response
    return EvaluationResponse(
        id=str(db_evaluation.id),
        evaluator={"id": str(current_user.id), "ho_ten": current_user.ho_ten},
        student={"id": str(student.id), "ho_ten": student.ho_ten},
        project={"id": str(project.id), "title": project.title},
        score=db_evaluation.score,
        comment=db_evaluation.comment
    )

@router.delete("/{evaluation_id}",
               description="Delete an evaluation. Only the evaluator can delete their evaluation.",
               summary="Delete an evaluation")
async def delete_evaluation(evaluation_id: str, current_user: User = Depends(get_current_user)):
    # Validate and get evaluation
    try:
        evaluation_id_obj = PyObjectId.validate(evaluation_id)
        evaluation = await Evaluation.get(evaluation_id_obj)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation_id format")
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Check evaluator (handle both Link and User)
    evaluator_id = None
    if isinstance(evaluation.evaluator, Link):
        evaluator_id = evaluation.evaluator.ref.id if evaluation.evaluator.ref else None
    elif isinstance(evaluation.evaluator, User):
        evaluator_id = evaluation.evaluator.id

    if not evaluator_id:
        logger.error(f"Invalid evaluator reference for evaluation {evaluation.id}")
        raise HTTPException(status_code=404, detail="Evaluator associated with evaluation not found")

    # Fetch evaluator only if it is a Link
    evaluator = evaluation.evaluator if isinstance(evaluation.evaluator, User) else await evaluation.evaluator.fetch()
   

    await evaluation.delete()
    logger.info(f"Deleted evaluation: {evaluation_id}")
    return {"message": "Evaluation deleted"}