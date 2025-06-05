from fastapi import HTTPException
from config import env
from github import Github
from github.GithubException import GithubException
from requests.exceptions import RetryError

class GitHubService:
    def __init__(self):
        self.github = Github(env.GITHUB_TOKEN)
    
    def get_user_info(self, username=None):
        if username:
            user = self.github.get_user(username)
        else:
            user = self.github.get_user()
        # Trả về dict chỉ chứa các trường cơ bản, không dùng __dict__
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
            if not commit.commit.message.startswith("Merge") and not commit.commit.message.startswith("Update"):
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
            print(f"Lỗi GithubException: {e.data}")
        except RetryError as re:
            print("Lỗi RetryError:", str(re))
        except Exception as ex:
            print("Lỗi không xác định:", str(ex))                
    
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
            valid_commits = self.get_repo_commits(repo_name, username)

            # Ánh xạ các tên author đặc biệt
            author_map = {
                "Khiempg": "Khiempg225868",
                "Bùi Ngọc Hợp": "hopite601",
                "Vu Quang Dung": "vqdung71104"
            }

            # Lấy login contributor
            login_user = [{"login": c["login"], "name": c["name"]} for c in self.get_repo_contributors(repo_name, username)]

            # Tạo tập hợp authors đã lọc và chuẩn hóa
            authors = {
                author_map.get(c["author"], c["author"])
                for c in valid_commits
                if c["author"] != "Unknown"
            }

            for commit in commits:
                raw_author = commit.commit.author.name
                if not raw_author:
                    continue

                # Chuẩn hóa tên author
                author = author_map.get(raw_author, raw_author)

                if author not in authors:
                    continue

                if author not in contributors:
                    contributors[author] = {
                        "contributor": author,
                        "messages": [],
                        "commit_count": 0,
                        "lines_added": 0,
                        "lines_removed": 0,
                        "files_modified": 0,
                        "last_commit_date": None
                    }

                if not commit.commit.message.startswith("Merge") and not commit.commit.message.startswith("Update"):
                    contributors[author]["messages"].append(commit.commit.message)

                contributors[author]["commit_count"] += 1
                contributors[author]["last_commit_date"] = commit.commit.author.date.isoformat() if commit.commit.author.date else None

                try:
                    full_commit = repo.get_commit(commit.sha)
                    contributors[author]["lines_added"] += full_commit.stats.additions
                    contributors[author]["lines_removed"] += full_commit.stats.deletions
                    contributors[author]["files_modified"] += len(full_commit.files)
                except Exception:
                    continue

            # Trả về dạng mảng
            return list(contributors.values())

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error analyzing repository: {str(e)}")