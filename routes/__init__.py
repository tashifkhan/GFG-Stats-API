from routes.docs import docs_router
from routes.badges import router as badges_router
from routes.contests import router as contests_router
from routes.heatmap import router as heatmap_router
from routes.legacy import router as legacy_router
from routes.profile import router as profile_router
from routes.rating import router as rating_router
from routes.stats import router as stats_router
from routes.summary import router as summary_router

__all__ = [
    "badges_router",
    "contests_router",
    "docs_router",
    "heatmap_router",
    "legacy_router",
    "profile_router",
    "rating_router",
    "stats_router",
    "summary_router",
]
