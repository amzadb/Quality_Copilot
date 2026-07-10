"""Dashboard activity feed. Implementation pending."""

from app.core.errors import not_implemented_yet


class ActivityService:
    async def get_recent(self, limit: int = 20):
        not_implemented_yet(
            "Recent activity feed",
            f"Fetching recent activity (limit={limit}) is not implemented yet. Requires run history storage.",
        )

    async def get_summary(self):
        not_implemented_yet(
            "Activity summary",
            "Dashboard metrics summary is not implemented yet. Requires aggregated run statistics.",
        )


def get_activity_service():
    return ActivityService()
