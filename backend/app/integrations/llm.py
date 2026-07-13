"""LLM integration — prompt templates and structured output parsing."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from fastapi import Depends
from pydantic import BaseModel, Field

from app.config import settings
from app.core.credential_store import CredentialStore, get_credential_store
from app.core.errors import AppError
from app.integrations._http import connection_failed, connection_ok, request_json
from app.schemas.common import ConnectionTestResponse, ReviewSeverity, TestCaseType
from app.schemas.jira import JiraTicketResponse
from app.schemas.pull_requests import PullRequestResponse


class GeneratedTestCase(BaseModel):
    id: str = Field(description="Local case ID, e.g. TC-01")
    title: str
    type: TestCaseType
    steps: list[str]
    expected_result: str


class TestCaseGenerationOutput(BaseModel):
    test_cases: list[GeneratedTestCase]


class GeneratedReviewComment(BaseModel):
    file: str
    line: int
    severity: ReviewSeverity
    comment: str


class CodeReviewOutput(BaseModel):
    comments: list[GeneratedReviewComment]


TEST_CASE_SYSTEM_PROMPT = """\
You are a senior QA engineer. Generate thorough, actionable test cases from a JIRA ticket.
Return JSON matching the TestCaseGenerationOutput schema.
Cover functional, edge-case, and negative scenarios where appropriate.
Respond with ONLY valid JSON — no markdown fences or commentary.
"""

TEST_CASE_USER_PROMPT = """\
Ticket: {ticket_key}
Title: {title}
Description:
{description}

Acceptance criteria:
{acceptance_criteria}
"""

CODE_REVIEW_SYSTEM_PROMPT = """\
You are a senior code reviewer. Analyze the pull request diff and return structured review comments.
Return JSON matching the CodeReviewOutput schema.
Focus on bugs, reliability issues, and meaningful style concerns.
Respond with ONLY valid JSON — no markdown fences or commentary.
"""

CODE_REVIEW_USER_PROMPT = """\
Repository: {repo}
PR #{pr_number}: {title}
Files changed: {files_changed} (+{additions}/-{deletions})

Diff:
{diff}
"""


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    return json.loads(cleaned)


class LLMIntegration:
    def __init__(self, credentials: CredentialStore) -> None:
        self._credentials = credentials

    def _api_key(self) -> str:
        section = self._credentials.get_section("llm")
        provider = section.get("provider") or "claude"
        token = section.get("token")
        if provider != "claude":
            raise AppError(
                status_code=501,
                code="LLM_PROVIDER_UNSUPPORTED",
                message=f"LLM provider '{provider}' is not implemented yet.",
            )
        if not token:
            raise AppError(
                status_code=400,
                code="LLM_NOT_CONFIGURED",
                message="LLM provider is not configured. Set an API key in Settings.",
            )
        return token

    def _anthropic_headers(self, api_key: str) -> dict[str, str]:
        return {
            "x-api-key": api_key,
            "anthropic-version": settings.anthropic_api_version,
            "content-type": "application/json",
        }

    async def _complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        api_key = self._api_key()
        body = {
            "model": settings.anthropic_model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        payload = await request_json(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers=self._anthropic_headers(api_key),
            json=body,
            timeout=120.0,
        )
        content_blocks = payload.get("content") or []
        text_parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        if not text_parts:
            raise AppError(
                status_code=502,
                code="LLM_EMPTY_RESPONSE",
                message="LLM returned an empty response.",
            )
        return _extract_json("\n".join(text_parts))

    async def generate_test_cases(self, ticket: JiraTicketResponse) -> TestCaseGenerationOutput:
        acceptance = ticket.acceptance_criteria or []
        acceptance_text = "\n".join(f"- {item}" for item in acceptance) if acceptance else "None provided"
        user_prompt = TEST_CASE_USER_PROMPT.format(
            ticket_key=ticket.key,
            title=ticket.title,
            description=ticket.description,
            acceptance_criteria=acceptance_text,
        )
        try:
            payload = await self._complete_json(TEST_CASE_SYSTEM_PROMPT, user_prompt)
            return TestCaseGenerationOutput.model_validate(payload)
        except AppError:
            raise
        except (json.JSONDecodeError, ValueError) as exc:
            raise AppError(
                status_code=502,
                code="LLM_PARSE_FAILED",
                message="Failed to parse LLM test case output as JSON.",
                details={"reason": str(exc)},
            ) from exc

    async def generate_review(self, pull_request: PullRequestResponse) -> CodeReviewOutput:
        user_prompt = CODE_REVIEW_USER_PROMPT.format(
            repo=pull_request.repo,
            pr_number=pull_request.pr_number,
            title=pull_request.title,
            files_changed=pull_request.files_changed,
            additions=pull_request.additions,
            deletions=pull_request.deletions,
            diff=pull_request.diff[:120000],
        )
        try:
            payload = await self._complete_json(CODE_REVIEW_SYSTEM_PROMPT, user_prompt)
            return CodeReviewOutput.model_validate(payload)
        except AppError:
            raise
        except (json.JSONDecodeError, ValueError) as exc:
            raise AppError(
                status_code=502,
                code="LLM_PARSE_FAILED",
                message="Failed to parse LLM code review output as JSON.",
                details={"reason": str(exc)},
            ) from exc

    async def test_connection(self) -> ConnectionTestResponse:
        try:
            api_key = self._api_key()
        except AppError as exc:
            return connection_failed(exc.code, str(exc.detail))

        try:
            await request_json(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers=self._anthropic_headers(api_key),
                json={
                    "model": settings.anthropic_model,
                    "max_tokens": 16,
                    "messages": [{"role": "user", "content": "Reply with OK"}],
                },
                timeout=30.0,
            )
        except AppError as exc:
            if exc.code == "AUTH_FAILED":
                return connection_failed("LLM_AUTH_FAILED", "LLM authentication failed.")
            return connection_failed("LLM_CONNECTION_FAILED", str(exc.detail))
        except httpx.HTTPError as exc:
            return connection_failed("LLM_CONNECTION_FAILED", str(exc))

        return connection_ok()


def get_llm_integration(
    credentials: CredentialStore = Depends(get_credential_store),
) -> LLMIntegration:
    return LLMIntegration(credentials)
