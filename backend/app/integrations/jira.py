"""JIRA REST integration — fetch tickets, post comments, attach files."""

from __future__ import annotations

from typing import Any

import httpx

from fastapi import Depends

from app.config import settings
from app.core.credential_store import CredentialStore, get_credential_store
from app.core.errors import AppError
from app.integrations._http import (
    connection_failed,
    connection_ok,
    normalize_base_url,
    request_json,
)
from app.schemas.common import ConnectionTestResponse
from app.schemas.jira import JiraAttachmentRequest, JiraAttachmentResponse, JiraTicketResponse


def _adf_to_text(node: Any) -> str:
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if node.get("type") == "text":
        return node.get("text", "")
    parts: list[str] = []
    for child in node.get("content") or []:
        parts.append(_adf_to_text(child))
    if node.get("type") in {"paragraph", "heading", "listItem"}:
        parts.append("\n")
    return "".join(parts).strip()


def _parse_ticket_payload(ticket_key: str, payload: dict[str, Any], base_url: str) -> JiraTicketResponse:
    fields = payload.get("fields", {})
    description_raw = fields.get("description")
    if isinstance(description_raw, dict):
        description = _adf_to_text(description_raw)
    else:
        description = str(description_raw or "")

    issue_type = fields.get("issuetype", {}).get("name", "Story")
    return JiraTicketResponse(
        key=payload.get("key", ticket_key),
        title=fields.get("summary", ""),
        description=description,
        acceptance_criteria=None,
        issue_type=issue_type,
        url=f"{base_url}/browse/{payload.get('key', ticket_key)}",
    )


class JiraIntegration:
    def __init__(self, credentials: CredentialStore) -> None:
        self._credentials = credentials

    def _config(self) -> tuple[str, tuple[str, str]]:
        section = self._credentials.get_section("jira")
        base_url = section.get("base_url")
        token = section.get("token")
        email = settings.jira_email

        if not base_url or not token:
            raise AppError(
                status_code=400,
                code="JIRA_NOT_CONFIGURED",
                message="JIRA is not configured. Set base URL and API token in Settings.",
            )
        if not email:
            raise AppError(
                status_code=400,
                code="JIRA_NOT_CONFIGURED",
                message="JIRA email is not configured. Set JIRA_EMAIL in the server environment.",
            )

        normalized = normalize_base_url(base_url)
        return normalized, (email, token)

    async def fetch_ticket(self, ticket_key: str) -> JiraTicketResponse:
        base_url, auth = self._config()
        url = f"{base_url}/rest/api/3/issue/{ticket_key.upper()}"
        try:
            payload = await request_json("GET", url, auth=auth)
        except AppError as exc:
            if exc.code == "NOT_FOUND":
                raise AppError(
                    status_code=404,
                    code="JIRA_NOT_FOUND",
                    message=f"JIRA ticket '{ticket_key}' was not found.",
                ) from exc
            if exc.code == "AUTH_FAILED":
                raise AppError(
                    status_code=401,
                    code="JIRA_AUTH_FAILED",
                    message="JIRA authentication failed. Check API token and JIRA_EMAIL.",
                ) from exc
            raise AppError(
                status_code=exc.status_code,
                code="JIRA_FETCH_FAILED",
                message=str(exc.detail),
            ) from exc

        return _parse_ticket_payload(ticket_key.upper(), payload, base_url)

    async def post_comment(self, ticket_key: str, comment: str) -> None:
        base_url, auth = self._config()
        url = f"{base_url}/rest/api/3/issue/{ticket_key.upper()}/comment"
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment}],
                    }
                ],
            }
        }
        await request_json("POST", url, auth=auth, json=body)

    async def attach_file(
        self,
        ticket_key: str,
        filename: str,
        content: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        base_url, auth = self._config()
        url = f"{base_url}/rest/api/3/issue/{ticket_key.upper()}/attachments"
        headers = {"X-Atlassian-Token": "no-check"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                auth=auth,
                headers=headers,
                files={"file": (filename, content, content_type)},
            )

        if response.status_code in (401, 403):
            raise AppError(
                status_code=401,
                code="JIRA_AUTH_FAILED",
                message="JIRA authentication failed while uploading an attachment.",
            )
        if response.status_code >= 400:
            raise AppError(
                status_code=502,
                code="JIRA_ATTACHMENT_FAILED",
                message=f"Failed to attach file to JIRA (HTTP {response.status_code}).",
            )

        attachments = response.json()
        if attachments and isinstance(attachments, list):
            return str(attachments[0].get("id", ""))
        return ""

    async def attach_files(
        self,
        ticket_key: str,
        body: JiraAttachmentRequest,
        *,
        files: list[tuple[str, bytes]] | None = None,
    ) -> JiraAttachmentResponse:
        attached_names: list[str] = []
        attachment_ids: list[str] = []

        if body.comment:
            await self.post_comment(ticket_key, body.comment)

        for filename, content in files or []:
            attachment_id = await self.attach_file(ticket_key, filename, content)
            attached_names.append(filename)
            if attachment_id:
                attachment_ids.append(attachment_id)

        return JiraAttachmentResponse(
            attached_files=attached_names,
            jira_attachment_ids=attachment_ids,
        )

    async def test_connection(self) -> ConnectionTestResponse:
        try:
            base_url, auth = self._config()
        except AppError as exc:
            return connection_failed(exc.code, str(exc.detail))

        url = f"{base_url}/rest/api/3/myself"
        try:
            await request_json("GET", url, auth=auth)
        except AppError as exc:
            if exc.code == "AUTH_FAILED":
                return connection_failed("JIRA_AUTH_FAILED", "JIRA authentication failed.")
            return connection_failed("JIRA_CONNECTION_FAILED", str(exc.detail))
        except httpx.HTTPError as exc:
            return connection_failed("JIRA_CONNECTION_FAILED", str(exc))

        return connection_ok()


def get_jira_integration(
    credentials: CredentialStore = Depends(get_credential_store),
) -> JiraIntegration:
    return JiraIntegration(credentials)
