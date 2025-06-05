from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.free_rider import FreeRider
from models.group_model import Group
from models.user_model import User
from models.project_model import Project
from models.evaluation_model import Evaluation
from service.github_service import GitHubService
from service.github_service import GitHubService
from schemas.free_rider import FreeRiderResponse
from routes.user_routes import get_current_user
from beanie import Link
from bson import ObjectId
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter(
  prefix='/free_rider',
  tags=["Free Rider"],
  responses={404: {"description": "Not found"}}
)

def get_github_service():
    return GitHubService()
  
@router.get(
    "/get_free_rider", 
    # response_model=list[FreeRiderResponse]
)
async def get_free_rider(
    group_id: str = Query(..., description="Group ID to filter free riders"),
    github_service: GitHubService = Depends(get_github_service)
):
    try:
        logger.info(f"Received request to get free riders for group_id: {group_id}")
        group_obj_id = ObjectId(group_id)
        
        logger.debug("Fetching group from database...")
        group = await Group.get(group_obj_id)
        if not group:
            logger.warning(f"Group with ID {group_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
                
        members = []
        if group.members:
            logger.debug("Fetching group members...")
            for member in group.members:
                if isinstance(member, Link):
                    fetched_member = await member.fetch() 
                else:
                    fetched_member = member 
                members.append(fetched_member)
        logger.info(f"Fetched {len(members)} members from group {group.name}")
        
        logger.debug("Fetching project information...")
        project = await group.project.fetch() if isinstance(group.project, Link) else group.project
        
        github_link = group.github_link
        if not github_link:
            logger.warning(f"Group {group.name} does not have a GitHub link.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group does not have a GitHub link")        
        
        logger.info(f"Fetching GitHub contributors for repo: {github_link}")
        reponame = github_link.split("/")[-1]
        username = github_link.split("/")[-2]
        
        contributors = None
        try:
            contributors = await github_service.analyze_contributor_activity(reponame, username)
        except Exception as e:
            logger.exception("Github API limit exceeded")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
        logger.debug(f"Found {len(contributors)} contributors in GitHub repo.")
        for c in contributors:
            c["loc"] = c["lines_added"] + c["lines_removed"]
        max_loc = max((c["loc"] for c in contributors), default=1)
        min_loc = min((c["loc"] for c in contributors), default=0)
        
        logger.info("Removing existing free riders from the database...")
        group_free_riders = await FreeRider.find(FreeRider.group._id == group_obj_id).to_list()
        if group_free_riders:
            for fr in group_free_riders:
                await fr.delete()
        logger.debug(f"Deleted {len(group_free_riders)} previous free riders")

        project_id = project.id if isinstance(project, Project) else project
        
        logger.info("Calculating new free rider scores...")
        for student in members:                    
            logger.debug(f"Processing student: {student.email}")
            student_evals = await Evaluation.find(
                Evaluation.project._id == ObjectId(project_id),
                Evaluation.student._id == ObjectId(student.id)
            ).to_list()
            logger.debug(f"Found {len(student_evals)} evaluations for student {student.email}")

            avg_score = sum(e.score for e in student_evals if e.score is not None) / len(student_evals) if student_evals else 0                
                        
            contributor_data = next((c for c in contributors if c["contributor"] == student.github_user), None)

            if contributor_data:
                loc_score = (contributor_data["loc"] - min_loc) / (max_loc - min_loc) if max_loc != min_loc else 0
                real_score = loc_score * 2 + avg_score * 0.8
            else:
                real_score = 0

            if real_score < 2:                
                freerider = FreeRider(
                    score=real_score,
                    user=Link(student),
                    group=Link(group),
                    commit_count=contributor_data["commit_count"] if contributor_data else 0,
                    lines_added=contributor_data["lines_added"] if contributor_data else 0,
                    lines_removed=contributor_data["lines_removed"] if contributor_data else 0,
                    files_modified=contributor_data["files_modified"] if contributor_data else 0,
                    last_commit_date=datetime.fromisoformat(contributor_data["last_commit_date"]) if contributor_data and contributor_data["last_commit_date"] else None
                )
                await freerider.insert()
                logger.info(f"Added free rider: {student.email} to group {group.name} with score {real_score:.2f}")

        logger.debug("Fetching final free rider list to return...")
        freeriders = await FreeRider.find(FreeRider.group._id == group_obj_id).to_list()
        logger.info(f"Total free riders identified: {len(freeriders)}")

        return [
            FreeRiderResponse(
                score=fr.score,
                user=await fr.user.fetch() if fr.user else None,
                group=await fr.group.fetch() if fr.group else None,
                commit_count=fr.commit_count,
                lines_added=fr.lines_added,
                lines_removed=fr.lines_removed,
                files_modified=fr.files_modified,
                last_commit_date=fr.last_commit_date.isoformat() if fr.last_commit_date else None
            ) for fr in freeriders
        ]        
    except Exception as e:
        logger.exception("Unhandled error while getting free rider contributors")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/all/free_rider"
)
async def get_all_free_rider(
    group_id: str = Query(..., description="Group ID to filter free riders"),
):
    freeriders = await FreeRider.find(FreeRider.group._id == ObjectId(group_id)).to_list()
    return freeriders