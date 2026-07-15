"""Code review page — fetch PR diff and run AI review."""

import asyncio
from typing import Any

import httpx
from nicegui import ui

from app.api.client import MOCK_PULL_REQUEST, api_client
from app.components.layout import page_shell
from app.components.review_comment_card import review_comment_card
from app.components.status_banner import status_banner

PROVIDER_LABELS: dict[str, str] = {
    "bitbucket": "Bitbucket",
    "github": "GitHub",
    "gitlab": "GitLab",
}


async def render_code_review() -> None:
    if not page_shell("/code-review"):
        return

    state: dict[str, Any] = {
        "pr": None,
        "run": None,
        "reviewing": False,
    }

    with ui.column().classes("page-content page-stack w-full gap-0"):
        with ui.element("div").classes("page-section--title w-full"):
            ui.label("Review a pull request").classes("page-title")

        with ui.element("div").classes("page-section--fetch w-full"):
            with ui.element("div").classes("ticket-fetch-row"):
                pr_input = ui.input(
                    value="bitbucket.org/acme/payments/pull-requests/318",
                    placeholder="Paste PR URL or repo path",
                ).classes("pr-url-input").props("outlined dense")
                fetch_button = ui.button("Fetch diff", icon="download").props("outline no-caps")

        with ui.element("div").classes("page-section--ticket w-full"):
            pr_container = ui.column().classes("w-full")
            pr_container.set_visibility(False)

        with ui.element("div").classes("page-section--loading w-full"):
            loading_container = ui.column().classes("w-full")
            loading_container.set_visibility(False)

        with ui.element("div").classes("page-section--results w-full"):
            comments_container = ui.column().classes("w-full")
            comments_container.set_visibility(False)

        def _provider_label(provider: str) -> str:
            return PROVIDER_LABELS.get(provider, provider.title())

        async def show_pr(pr: dict[str, Any]) -> None:
            state["pr"] = pr
            pr_container.clear()
            with pr_container:
                with ui.element("div").classes("pr-card w-full"):
                    ui.label(f"#{pr['pr_number']} · {pr['title']}").classes("pr-card-title")

                    with ui.element("div").classes("pr-card-stats"):
                        ui.label(
                            f"{pr['files_changed']} files changed · "
                            f"+{pr['additions']} −{pr['deletions']} ·"
                        )
                        with ui.element("span").classes("pr-provider"):
                            ui.icon("call_merge").classes("text-sm")
                            ui.label(_provider_label(pr.get("provider", "bitbucket")))

                    async def on_review() -> None:
                        if state["reviewing"]:
                            return
                        state["reviewing"] = True
                        loading_container.clear()
                        with loading_container:
                            status_banner("Analyzing diff with Claude...")
                        loading_container.set_visibility(True)
                        comments_container.set_visibility(False)

                        try:
                            run = await api_client.generate_review(pr["repo"], pr["pr_number"])
                        except httpx.HTTPError as exc:
                            ui.notify(f"Review failed: {exc}", type="negative")
                            loading_container.set_visibility(False)
                            return
                        finally:
                            state["reviewing"] = False

                        if run.get("run_id", "").startswith("demo-"):
                            await asyncio.sleep(1.5)

                        loading_container.set_visibility(False)
                        state["run"] = run
                        show_comments(run)

                    ui.button("Run AI review", icon="auto_awesome", on_click=on_review).props(
                        "no-caps unelevated"
                    ).classes("btn-generate")

            pr_container.set_visibility(True)

        def show_comments(run: dict[str, Any]) -> None:
            comments = run.get("comments", [])
            run_id = run.get("run_id")

            def _on_triage_change(updated: dict[str, Any]) -> None:
                if not state.get("run"):
                    return
                run_comments = state["run"].get("comments", [])
                for index, item in enumerate(run_comments):
                    if item.get("id") == updated.get("id"):
                        run_comments[index] = updated
                        break

            comments_container.clear()
            with comments_container:
                with ui.element("div").classes("review-comments-panel w-full"):
                    ui.label(f"Review comments ({len(comments)})").classes("review-comments-title")
                    for comment in comments:
                        review_comment_card(
                            comment,
                            run_id=run_id,
                            on_triage_change=_on_triage_change,
                        )

            comments_container.set_visibility(True)

        async def on_fetch() -> None:
            url = (pr_input.value or "").strip()
            if not url:
                ui.notify("Enter a pull request URL", type="warning")
                return
            try:
                pr = await api_client.fetch_pull_request(url=url)
            except httpx.HTTPError:
                ui.notify("Backend unreachable — using demo PR data", type="warning")
                pr = MOCK_PULL_REQUEST.copy()
            await show_pr(pr)

        fetch_button.on_click(on_fetch)

        def _auto_fetch() -> None:
            asyncio.create_task(on_fetch())

        ui.timer(0.05, _auto_fetch, once=True)
