from fastapi import HTTPException
from config import env
from github import Github
from datetime import datetime, timedelta
import pytz
class GitHubService:
    def __init__(self):
        self.github = Github(env.GITHUB_TOKEN)
    
    def get_user_repositories(self, username=None):
        """Lấy danh sách repositories của user hoặc người dùng hiện tại"""
        if username:
            user = self.github.get_user(username)
        else:
            user = self.github.get_user()
        
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
        """Lấy danh sách commits của repository"""
        if username:
            repo = self.github.get_repo(f"{username}/{repo_name}")
        else:
            user = self.github.get_user()
            repo = self.github.get_repo(f"{user.login}/{repo_name}")
        
        commits = []
        for commit in repo.get_commits():
            commits.append({
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat()
            })
        return commits
    
    def get_repo_contributors(self, repo_name, username=None):
        """Lấy danh sách contributors của repository"""
        if username:
            repo = self.github.get_repo(f"{username}/{repo_name}")
        else:
            user = self.github.get_user()
            repo = self.github.get_repo(f"{user.login}/{repo_name}")
        
        contributors = []
        for contributor in repo.get_contributors():
            contributors.append({
                "login": contributor.login,
                "contributions": contributor.contributions,
                "avatar_url": contributor.avatar_url,
                "profile_url": contributor.html_url
            })
        return contributors
    
    def analyze_contributor_activity(self, repo_name, username=None):
        """Phân tích hoạt động của các contributors"""
        try:
            if username:
                repo = self.github.get_repo(f"{username}/{repo_name}")
            else:
                user = self.github.get_user()
                repo = self.github.get_repo(f"{user.login}/{repo_name}")
            
            contributors = {}
            commits = repo.get_commits()
            
            for commit in commits:
                author = commit.commit.author.name
                if not author:
                    continue

                if author not in contributors:
                    contributors[author] = {
                        "commit_count": 0,
                        "lines_added": 0,
                        "lines_removed": 0,
                        "files_modified": 0,
                        "last_commit_date": None
                    }
                
                contributors[author]["commit_count"] += 1
                contributors[author]["last_commit_date"] = commit.commit.author.date

                try:
                    full_commit = repo.get_commit(commit.sha)
                    contributors[author]["lines_added"] += full_commit.stats.additions
                    contributors[author]["lines_removed"] += full_commit.stats.deletions
                    contributors[author]["files_modified"] += len(full_commit.files)
                except Exception:
                    continue

            return contributors
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error analyzing repository: {str(e)}")

    def dect_freelance_contributors(self, repo_name, username=None, min_inactive_days=30, max_commit_count=10,max_activity_span_days=14):
        try:
            if username:
                repo = self.github.get_repo(f"{username}/{repo_name}")
            else:
                user = self.github.get_user()
                repo = self.github.get_repo(f"{username}/{repo_name}")
            
            #Lấy tất cả commit từ respository
            all_commits = list(repo.get_commits())
            
            #Phân tích dữ liệu commit theo author
            authors_data = {}
            for commit in all_commits:
                authors_name = commit.commit.author.name
                commit_date = commit.commit.author.date
                if not authors_name:
                    continue
                
                if authors_name not in authors_data:
                    authors_data[authors_name] = {
                        "commits": [],
                        "first_commit_date": None,
                        "last_commit_date": None,
                        "commit_count": 0,
                        "active_days": set()
                    }        
                
                authors_data[authors_name]["commits"].append(commit_date)
                authors_data[authors_name]["commit_count"] += 1
                authors_data[authors_name]["active_days"].add(commit_date.date())
                
                #cập nhật ngày commit đầu tiên và cuối cùng
                if(authors_data[authors_name]["first_commit_date"] is None or commit_date < authors_data[authors_name]["first_commit_date"]):
                    authors_data[authors_name]["first_commit_date"] = commit_date
                if(authors_data[authors_name]["last_commit_date"] is None or commit_date > authors_data[authors_name]["last_commit_date"]):
                    authors_data[authors_name]["last_commit_date"] = commit_date
            
            #phân tích để tìm thành viên tự do
            freelancers = {}
            now = datetime.now(pytz.utc)
            
            for author, data in authors_data.items():
                #số ngày không hoạt động (tính từ lần commit cuối)
                if data["last_commit_date"]:
                    days_since_last_commit = (now - data["last_commit_date"]).days
                else:
                    days_since_last_commit = 0
                
                #tính thời gian hoạt động (từ commit đầu đến commit cuối)
                activity_span = 0
                if data["first_commit_date"] and data["last_commit_date"]:
                    activity_span = (data["last_commit_date"] - data["first_commit_date"]).days
                
                #số ngày thực sự có hoạt động commit
                activity_days_count = len(data["active_days"])
                
                #xác định thành viên tự do dựa trên các tiêu chí
                is_freelancer = (
                    days_since_last_commit >= min_inactive_days and #Không hoạt động trong một thời gian
                    data["commit_count"] <= max_commit_count and # Số lượng commit ít
                    activity_span <= max_activity_span_days #khoảng thời gian hoạt động ngắn
                )
                
                if is_freelancer:
                    freelancers[author] = {
                        "commit_count": data["commit_count"],
                        "first_commit": data["first_commit_date"].isoformat() if data["first_commit_date"] else None,
                        "last_commit": data["last_commit_date"].isoformat() if data["last_commit_date"] else None,
                        "days_since_last_commit": days_since_last_commit,
                        "activity_span_days": activity_span,
                        "activity_days_count": activity_days_count,
                        "commit_frequency": data["commit_count"] / (activity_span if activity_span > 0 else 1)
                    }
            return {
                "freelancers": freelancers,
                "total_contributors": len(authors_data),
                "freelancers_count": len(freelancers)
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error detecting freelance contributors: {str(e)}")
