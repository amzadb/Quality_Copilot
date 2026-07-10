from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ConnectionTestSuccess(BaseModel):
    ok: Literal[True] = True


class ConnectionTestFailure(BaseModel):
    ok: Literal[False] = False
    error: ErrorDetail


ConnectionTestResponse = ConnectionTestSuccess | ConnectionTestFailure

IntegrationName = Literal["jira", "git_provider", "testrail", "llm"]
ExportFormat = Literal["docx", "csv"]
TestCaseType = Literal["functional", "edge_case", "negative"]
ReviewSeverity = Literal["high", "medium", "style"]
CommentTriageStatus = Literal["dismissed", "addressed"]
GitProviderType = Literal["bitbucket", "github", "gitlab"]
LLMProvider = Literal["claude"]
