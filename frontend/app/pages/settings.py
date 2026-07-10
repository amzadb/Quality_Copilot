"""Settings page — integration configuration."""

import asyncio
from typing import Any

import httpx
from nicegui import ui

from app.api.client import api_client
from app.components.layout import page_shell

GIT_PROVIDER_OPTIONS = {
    "bitbucket": "Bitbucket",
    "github": "GitHub",
    "gitlab": "GitLab",
}

LLM_PROVIDER_OPTIONS = {
    "claude": "Claude",
}


def _wire_test_connection(integration: str, button: ui.button, status_label: ui.label) -> None:
    async def on_test() -> None:
        button.props("loading")
        status_label.text = ""
        status_label.classes(
            remove="integration-test-status--ok integration-test-status--error"
        )
        try:
            result = await api_client.test_integration(integration)
        except httpx.HTTPError as exc:
            status_label.text = f"Error: {exc}"
            status_label.classes(add="integration-test-status--error")
        else:
            if result.get("ok"):
                status_label.text = "Connection OK"
                status_label.classes(add="integration-test-status--ok")
            else:
                error = result.get("error") or {}
                status_label.text = error.get("message", "Connection failed")
                status_label.classes(add="integration-test-status--error")
        finally:
            button.props(remove="loading")

    button.on_click(on_test)


async def render_settings() -> None:
    page_shell("/settings")

    with ui.column().classes("page-content w-full gap-0"):
        ui.label("Integrations").classes("page-title")

        # --- JIRA ---
        with ui.element("div").classes("integration-card w-full"):
            with ui.element("div").classes("integration-header"):
                ui.icon("extension").classes("text-xl text-gray-600")
                ui.label("JIRA").classes("integration-title")
            with ui.element("div").classes("integration-row"):
                jira_base_url = ui.input(placeholder="acme.atlassian.net").classes("integration-field").props(
                    "outlined dense"
                )
                jira_token = ui.input(placeholder="API token").classes("integration-field").props(
                    "outlined dense type=password"
                )
            with ui.element("div").classes("integration-test-row"):
                jira_test_btn = ui.button("Test connection", icon="lan").props("outline no-caps dense")
                jira_test_status = ui.label("").classes("integration-test-status")

        # --- Git provider ---
        with ui.element("div").classes("integration-card w-full"):
            with ui.element("div").classes("integration-header"):
                ui.icon("shield").classes("text-xl text-gray-600")
                ui.label("Git provider").classes("integration-title")
            with ui.element("div").classes("integration-row"):
                git_type = ui.select(GIT_PROVIDER_OPTIONS, value="bitbucket").classes("integration-field").props(
                    "outlined dense"
                )
                git_workspace = ui.input(placeholder="acme").classes("integration-field").props("outlined dense")
            with ui.element("div").classes("integration-row"):
                git_token = ui.input(placeholder="App password / access token").classes(
                    "integration-field--full w-full"
                ).props("outlined dense type=password")
            with ui.element("div").classes("integration-test-row"):
                git_test_btn = ui.button("Test connection", icon="lan").props("outline no-caps dense")
                git_test_status = ui.label("").classes("integration-test-status")

        # --- TestRail ---
        with ui.element("div").classes("integration-card w-full"):
            with ui.element("div").classes("integration-header"):
                ui.icon("assignment").classes("text-xl text-gray-600")
                ui.label("TestRail").classes("integration-title")
            with ui.element("div").classes("integration-row"):
                testrail_base_url = ui.input(placeholder="acme.testrail.io").classes("integration-field").props(
                    "outlined dense"
                )
                testrail_username = ui.input(placeholder="Username / email").classes("integration-field").props(
                    "outlined dense"
                )
            with ui.element("div").classes("integration-row"):
                testrail_token = ui.input(placeholder="API key").classes("integration-field--full w-full").props(
                    "outlined dense type=password"
                )
            with ui.element("div").classes("integration-test-row"):
                testrail_test_btn = ui.button("Test connection", icon="lan").props("outline no-caps dense")
                testrail_test_status = ui.label("").classes("integration-test-status")

        # --- LLM provider ---
        with ui.element("div").classes("integration-card w-full"):
            with ui.element("div").classes("integration-header"):
                ui.icon("auto_awesome").classes("text-xl text-gray-600")
                ui.label("LLM provider").classes("integration-title")
            with ui.element("div").classes("integration-row"):
                llm_provider = ui.select(LLM_PROVIDER_OPTIONS, value="claude").classes("integration-field").props(
                    "outlined dense"
                )
                llm_token = ui.input(placeholder="API key").classes("integration-field").props(
                    "outlined dense type=password"
                )
            with ui.element("div").classes("integration-test-row"):
                llm_test_btn = ui.button("Test connection", icon="lan").props("outline no-caps dense")
                llm_test_status = ui.label("").classes("integration-test-status")

        with ui.element("div").classes("settings-save-row"):
            save_button = ui.button("Save settings", icon="save").props("no-caps unelevated").classes("btn-generate")

        _wire_test_connection("jira", jira_test_btn, jira_test_status)
        _wire_test_connection("git_provider", git_test_btn, git_test_status)
        _wire_test_connection("testrail", testrail_test_btn, testrail_test_status)
        _wire_test_connection("llm", llm_test_btn, llm_test_status)

        def _apply_settings(data: dict[str, Any]) -> None:
            jira = data.get("jira", {})
            if jira.get("base_url"):
                jira_base_url.value = jira["base_url"]
            if jira.get("token_set"):
                jira_token.props('placeholder="Token saved (enter to replace)"')

            git = data.get("git_provider", {})
            if git.get("type"):
                git_type.value = git["type"]
            if git.get("workspace"):
                git_workspace.value = git["workspace"]
            if git.get("token_set"):
                git_token.props('placeholder="Token saved (enter to replace)"')

            testrail = data.get("testrail", {})
            if testrail.get("base_url"):
                testrail_base_url.value = testrail["base_url"]
            if testrail.get("username"):
                testrail_username.value = testrail["username"]
            if testrail.get("token_set"):
                testrail_token.props('placeholder="API key saved (enter to replace)"')

            llm = data.get("llm", {})
            if llm.get("provider"):
                llm_provider.value = llm["provider"]
            if llm.get("token_set"):
                llm_token.props('placeholder="API key saved (enter to replace)"')

        async def load_settings() -> None:
            try:
                data = await api_client.get_settings()
            except httpx.HTTPError:
                ui.notify("Backend unreachable — showing default form", type="warning")
                data = await api_client.get_settings()
            _apply_settings(data)

        async def on_save() -> None:
            payload: dict[str, Any] = {
                "jira": {"base_url": (jira_base_url.value or "").strip() or None},
                "git_provider": {
                    "type": git_type.value,
                    "workspace": (git_workspace.value or "").strip() or None,
                },
                "testrail": {
                    "base_url": (testrail_base_url.value or "").strip() or None,
                    "username": (testrail_username.value or "").strip() or None,
                },
                "llm": {"provider": llm_provider.value},
            }

            if jira_token.value:
                payload["jira"]["token"] = jira_token.value
            if git_token.value:
                payload["git_provider"]["token"] = git_token.value
            if testrail_token.value:
                payload["testrail"]["token"] = testrail_token.value
            if llm_token.value:
                payload["llm"]["token"] = llm_token.value

            try:
                updated = await api_client.update_settings(payload)
            except httpx.HTTPError as exc:
                ui.notify(f"Save failed: {exc}", type="negative")
                return

            jira_token.value = ""
            git_token.value = ""
            testrail_token.value = ""
            llm_token.value = ""
            _apply_settings(updated)
            ui.notify("Settings saved", type="positive")

        save_button.on_click(on_save)

        def _auto_load() -> None:
            asyncio.create_task(load_settings())

        ui.timer(0.05, _auto_load, once=True)
