from fastapi import APIRouter, Depends, HTTPException
from service.github_service import GitHubService

router = APIRouter(
    prefix='/github',
    tags=["github"],
    responses={404: {"description": "Not found"}}
)

def get_github_service():
    return GitHubService()

@router.get('/repos')
async def get_repos(
    username: str = None, 
    github_service: GitHubService = Depends(get_github_service)
):
    try:
        return github_service.get_user_repositories(username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/repos/{username}/{repo_name}/commits')
async def get_repo_commits(
    username: str, 
    repo_name: str, 
    github_service: GitHubService = Depends(get_github_service)
):
    try:
        return github_service.get_repo_commits(repo_name,username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/repos/{username}/{repo_name}/contributors')
async def get_repo_contributors(
    username: str, 
    repo_name: str, 
    github_service: GitHubService = Depends(get_github_service)
):
    try:
        return github_service.get_repo_contributors(repo_name,username)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/repos/{username}/{repo_name}/analysis")
async def analyze_repo(
    username: str,
    repo_name: str,
    github_service: GitHubService = Depends(get_github_service)
):
    """Phân tích một kho lưu trữ GitHub"""
    try:
        contributors = github_service.analyze_contributor_activity(repo_name, username)
        return {"contributors": contributors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/repos/{username}/{repo_name}/freelancers")
async def detect_freelancers(
    username: str,
    repo_name: str,
    min_inactive_days: int = 30,
    max_commit_count: int = 10,
    max_activity_span_days: int = 14,
    github_service: GitHubService = Depends(get_github_service)
):
    """Phát hiện thành viên tự do"""
    try:
        freelancers = github_service.dect_freelance_contributors(
            repo_name,
            username,
            min_inactive_days,
            max_commit_count,
            max_activity_span_days
        )
        return freelancers
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))