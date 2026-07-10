from fastapi import APIRouter

from app.api.routes import activity, jira, pull_requests, reviews, settings, test_cases, testrail

api_router = APIRouter()
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(jira.router, prefix="/jira", tags=["JIRA"])
api_router.include_router(test_cases.router, prefix="/test-cases", tags=["Test Cases"])
api_router.include_router(testrail.router, prefix="/testrail", tags=["TestRail"])
api_router.include_router(pull_requests.router, prefix="/pull-requests", tags=["Pull Requests"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
api_router.include_router(activity.router, prefix="/activity", tags=["Dashboard"])
