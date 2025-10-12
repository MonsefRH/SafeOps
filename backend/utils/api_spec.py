from apispec import APISpec
from apispec_pydantic_plugin import PydanticPlugin

from schemas.user_dto import *
from schemas.admin_dto import *
from schemas.github_dto import *
from schemas.google_dto import *
from schemas.dashboard_dto import *
from schemas.full_scan_dto import *
from schemas.history_dto import *
from schemas.risks_dto import *
from schemas.semgrep_dto import *
from schemas.checkov_dto import *
from schemas.t5_dto import *

# Create custom APISpec with Pydantic plugin
spec = APISpec(
    title="SafeOps+ API Documentation",
    version="1.0.0",
    openapi_version="2.0",
    plugins=[PydanticPlugin()],  # Enables Pydantic schema generation
    info=dict(description="API docs for SafeOps project.")
)

# User-related
spec.components.schema("UserResponse", schema=UserResponse)
spec.components.schema("RegisterRequest", schema=RegisterRequest)
spec.components.schema("RegisterResponse", schema=RegisterResponse)
spec.components.schema("LoginRequest", schema=LoginRequest)
spec.components.schema("LoginResponse", schema=LoginResponse)
spec.components.schema("VerifyCodeRequest", schema=VerifyCodeRequest)
spec.components.schema("VerifyCodeResponse", schema=VerifyCodeResponse)
spec.components.schema("SetPasswordRequest", schema=SetPasswordRequest)
spec.components.schema("SetPasswordResponse", schema=SetPasswordResponse)
spec.components.schema("RefreshResponse", schema=RefreshResponse)
spec.components.schema("ErrorResponse", schema=ErrorResponse)

# Admin-related
spec.components.schema("UserStatsResponse", schema=UserStatsResponse)
spec.components.schema("AdminStatsResponse", schema=AdminStatsResponse)

# Dashboard-related
spec.components.schema("DashboardStatsResponse", schema=DashboardStatsResponse)
spec.components.schema("DashboardErrorResponse", schema=DashboardErrorResponse)

# Github-related
spec.components.schema("GithubRepo", schema=GithubRepo)
spec.components.schema("GithubCallbackResponse", schema=GithubCallbackResponse)
spec.components.schema("GithubValidateTokenRequest", schema=GithubValidateTokenRequest)
spec.components.schema("GithubValidateTokenResponse", schema=GithubValidateTokenResponse)
spec.components.schema("GithubSelectedRepo", schema=GithubSelectedRepo)
spec.components.schema("GithubSaveReposRequest", schema=GithubSaveReposRequest)
spec.components.schema("GithubSaveReposResponse", schema=GithubSaveReposResponse)
spec.components.schema("GithubRepoConfig", schema=GithubRepoConfig)
spec.components.schema("GithubErrorResponse", schema=GithubErrorResponse)

# Google-related
spec.components.schema("GoogleAuthResponse", schema=GoogleAuthResponse)
spec.components.schema("GoogleCallbackResponse", schema=GoogleCallbackResponse)
spec.components.schema("GoogleErrorResponse", schema=GoogleErrorResponse)

# Checkov-related
spec.components.schema("CheckovCheck", schema=CheckovCheck)
spec.components.schema("CheckovSummary", schema=CheckovSummary)
spec.components.schema("CheckovResponse", schema=CheckovResponse)
spec.components.schema("CheckovContentRequest", schema=CheckovContentRequest)
spec.components.schema("CheckovRepoRequest", schema=CheckovRepoRequest)
spec.components.schema("CheckovErrorResponse", schema=CheckovErrorResponse)

# Semgrep-related
spec.components.schema("SemgrepFinding", schema=SemgrepFinding)
spec.components.schema("SemgrepResult", schema=SemgrepResult)
spec.components.schema("SemgrepResponse", schema=SemgrepResponse)
spec.components.schema("SemgrepErrorResponse", schema=SemgrepErrorResponse)

# T5-related
spec.components.schema("T5Request", schema=T5Request)
spec.components.schema("T5Response", schema=T5Response)
spec.components.schema("T5ErrorResponse", schema=T5ErrorResponse)

# History-related
spec.components.schema("ScanHistoryResponse", schema=ScanHistoryResponse)
spec.components.schema("HistoryErrorResponse", schema=HistoryErrorResponse)

# Risks-related
spec.components.schema("RiskSummary", schema=RiskSummary)
spec.components.schema("RiskDetail", schema=RiskDetail)
spec.components.schema("RisksResponse", schema=RisksResponse)
spec.components.schema("RisksErrorResponse", schema=RisksErrorResponse)

# Full Scan-related (was under T5—corrected)
spec.components.schema("T5Correction", schema=T5Correction)
spec.components.schema("FullScanResponse", schema=FullScanResponse)
spec.components.schema("FullScanRequest", schema=FullScanRequest)
spec.components.schema("FullScanErrorResponse", schema=FullScanErrorResponse)

# Security definitions
spec.components.security_scheme("Bearer", {
    "type": "apiKey",
    "name": "Authorization",
    "in": "header"
})

# Export the spec Swagger
swagger_template = spec.to_dict()

swagger_template["tags"] = [
    {
        "name": "User Authentication",
        "description": "Endpoints for user registration, login, and token management."
    },
    {
        "name": "Dashboard",
        "description": "User dashboard statistics and overview."
    },
    {
        "name": "Admin",
        "description": "Admin-level statistics and management."
    },
    {
        "name": "T5 Correction",
        "description": "Dockerfile correction using T5 model."
    },
    {
        "name": "Semgrep Scan",
        "description": "Code validation with Semgrep."
    },
    {
        "name": "Risks",
        "description": "Security risks data retrieval."
    },
    {
        "name": "Scan History",
        "description": "User scan history queries."
    },
    {
        "name": "Google Authentication",
        "description": "Google OAuth login and callback."
    },
    {
        "name": "GitHub Authentication",
        "description": "GitHub OAuth login and callback."
    },
    {
        "name": "GitHub Repos",
        "description": "GitHub repository management and configs."
    },
    {
        "name": "Full Scan",
        "description": "Comprehensive security scans."
    },
    {
        "name": "Checkov Scan",
        "description": "IaC scans with Checkov (file, repo, content)."
    }
]
