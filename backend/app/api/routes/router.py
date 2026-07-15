from fastapi import APIRouter, Depends

from app.api.routes import activity, auth, jira, pull_requests, reviews, settings, test_cases, testrail
from app.core.deps import get_current_user

api_router = APIRouter()

# Public auth endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# All other v1 routes require a valid JWT
protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(settings.router, prefix="/settings", tags=["Settings"])
protected.include_router(jira.router, prefix="/jira", tags=["JIRA"])
protected.include_router(test_cases.router, prefix="/test-cases", tags=["Test Cases"])
protected.include_router(testrail.router, prefix="/testrail", tags=["TestRail"])
protected.include_router(pull_requests.router, prefix="/pull-requests", tags=["Pull Requests"])
protected.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
protected.include_router(activity.router, prefix="/activity", tags=["Dashboard"])
api_router.include_router(protected)
