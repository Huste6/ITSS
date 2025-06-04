from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models.free_rider import FreeRider
from models.group_model import Group
from models.user_model import User
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
  
@router.get("/get_free_rider", response_model=list[FreeRiderResponse])
async def get_free_rider(
    group_id: str = Query(..., description="Group ID to filter free riders"),
    github_service: GitHubService = Depends(get_github_service)
):
    try:
        group_obj_id = ObjectId(group_id)
        group = await Group.get(group_obj_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
                
        #Error
        members = []
        if group.members:
            for member in group.members:
                fetched_member = await member.fetch() if isinstance(member, Link) else member
                members.append(fetched_member)

        print(members)
        
        github_link = group.github_link
        if not github_link:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group does not have a GitHub link")
        
        reponame = github_link.split("/")[-1]
        username = github_link.split("/")[-2]
        contributors = await github_service.get_repo_contributors(reponame, username)
        
        for c in contributors:
            c["loc"] = c["lines_added"] + c["lines_removed"]
        max_loc = max((c["loc"] for c in contributors), default=1)
        min_loc = min((c["loc"] for c in contributors), default=0)

        project = await group.project.fetch()

        for student in members:
            student_evals = await Evaluation.find(
                Evaluation.project == Link(project),
                Evaluation.student == Link(student)
            ).to_list()

            avg_score = sum(e.score for e in student_evals if e.score is not None) / len(student_evals) if student_evals else 0

            contributor_data = next((c for c in contributors if c["contributor"] == student.github_user), None)

            if contributor_data:
                loc_score = (contributor_data["loc"] - min_loc) / (max_loc - min_loc) if max_loc != min_loc else 0
                real_score = loc_score * 2 + avg_score * 0.8
            else:
                real_score = 0

            if real_score < 2:
                await FreeRider.find(FreeRider.group == Link(group)).delete()

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
                logger.info(f"Added free rider: {student.username} to group {group.name}")

        freeriders = await FreeRider.find(FreeRider.group == Link(group)).to_list()
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
        logger.error(f"Error getting free rider contributors: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
