from pydantic import BaseModel
from typing import List, Optional, Dict

class GithubRepo(BaseModel):
    name: str
    full_name: str
    description: Optional[str]
    html_url: str
    has_dependabot: bool = False
    is_selected: bool = False

class GithubCallbackResponse(BaseModel):
    redirect_url: str

class GithubValidateTokenRequest(BaseModel):
    token: str
    selected_repos: Optional[List[str]] = None

class GithubValidateTokenResponse(BaseModel):
    message: str
    repos: List[GithubRepo]

class GithubSelectedRepo(BaseModel):
    full_name: str
    name: str
    html_url: str
    description: Optional[str] = None
    has_dependabot: bool = False
    is_selected: bool = False

class GithubSaveReposRequest(BaseModel):
    selected_repos: List[GithubSelectedRepo]

class GithubSaveReposResponse(BaseModel):
    message: str

class GithubRepoConfig(BaseModel):
    id: int
    file_path: str
    file_name: str
    content: str
    sha: str
    repo_full_name: str
    repo_html_url: str
    framework: str

class GithubErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None