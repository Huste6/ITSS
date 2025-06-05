from fastapi import HTTPException
from config import env
from github import Github
from github.GithubException import GithubException
from requests.exceptions import RetryError
import logging

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GitHubService:
    def __init__(self):
        self.github = Github(env.GITHUB_TOKEN)

    def get_repo(self, username: str, reponame: str):
        """Lấy repository theo username và tên repo"""
        try:
            return self.github.get_repo(f"{username}/{reponame}")
        except GithubException as e:
            logger.error(f"GitHubException: {e}")
            raise HTTPException(status_code=404, detail="Repository not found")
        except Exception as e:
            logger.error(f"Unexpected error in get_repo: {e}")
            raise HTTPException(status_code=400, detail="Could not fetch repository")

    def get_user_info(self, username=None):
        user = self.github.get_user(username) if username else self.github.get_user()
        return {
            "login": user.login,
            "id": user.id,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "html_url": user.html_url,
            "bio": user.bio,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    def get_user_repositories(self, username=None):
        user = self.github.get_user(username) if username else self.github.get_user()
        repos = []
        for repo in user.get_repos():
            repos.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "language": repo.language,
                "stars": repo.stargazers_count
            })
        return repos

    def get_repo_commits(self, repo_name, username=None):
        repo = self.get_repo(username, repo_name)
        commits = []
        for commit in repo.get_commits():
            if not commit.commit.message.startswith("Merge") and not commit.commit.message.startswith("Update"):
                commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat()
                })
        return commits

    def get_repo_contributors(self, repo_name, username=None):
        repo = self.get_repo(username, repo_name)
        try:
            contributors = []
            for contributor in repo.get_contributors():
                contributors.append({
                    "login": contributor.login,
                    "name": contributor.name,
                    "contributions": contributor.contributions,
                    "avatar_url": contributor.avatar_url,
                    "profile_url": contributor.html_url
                })
            return contributors
        except GithubException as e:
            logger.error(f"GitHubException: {e.data}")
            raise HTTPException(status_code=400, detail="GitHub API error")
        except RetryError as re:
            logger.error(f"RetryError: {str(re)}")
            raise HTTPException(status_code=400, detail="Retry error with GitHub API")
        except Exception as ex:
            logger.error(f"Unknown error: {str(ex)}")
            raise HTTPException(status_code=400, detail="Unknown error occurred")

    async def analyze_contributor_activity(self, reponame: str, username: str):
        try:
            repo = self.get_repo(username, reponame)
            contributor_data = {}

            for commit in repo.get_commits():
                author = commit.author.login if commit.author else "unknown"
                if author not in contributor_data:
                    contributor_data[author] = {
                        "contributor": author,
                        "commit_count": 0,
                        "lines_added": 0,
                        "lines_removed": 0,
                        "files_modified": 0,
                        "last_commit_date": None,
                    }

                contributor_data[author]["commit_count"] += 1
                full_commit = repo.get_commit(commit.sha)

                # Đếm số file thay đổi trong commit
                contributor_data[author]["files_modified"] += sum(1 for _ in full_commit.files)

                stats = full_commit.stats
                contributor_data[author]["lines_added"] += stats.additions
                contributor_data[author]["lines_removed"] += stats.deletions

                commit_date = full_commit.commit.author.date.isoformat() if full_commit.commit.author and full_commit.commit.author.date else None
                contributor_data[author]["last_commit_date"] = commit_date

            return list(contributor_data.values())

        except Exception as e:
            logger.exception("Error analyzing repository")
            raise HTTPException(status_code=400, detail=f"Error analyzing repository: {str(e)}")
