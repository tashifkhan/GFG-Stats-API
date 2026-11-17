"""Per-problem topic tag lookup for GFG solved problems.

GFG's solved-problem list (``services/profile.py::get_detailed_user_data``)
gives a slug per problem but no topic tags. Each problem's tags are fetched
individually from GFG's practice API and tallied into a topic breakdown. See
../CANONICAL_SCHEMA.md.

Enrichment is optional: it runs under one shared budget and is dropped rather
than extending the request past the platform's function limit.
"""

import asyncio
from typing import Any, Dict, List

import httpx

from config import settings
from models.canonical.stats import TopicCount

PROBLEM_URL = "https://practiceapi.geeksforgeeks.org/api/v1/problems/{slug}/"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.geeksforgeeks.org",
    "Referer": "https://www.geeksforgeeks.org/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

# Topic tags are static per problem, so caching them for the process lifetime
# is safe and avoids re-fetching the same problem across users/requests.
_TAG_CACHE: Dict[str, List[str]] = {}

# Ten concurrent lookups was the incident's fan-out; the budget, not this
# number, is what bounds total time.
_CONCURRENCY = 10


async def _fetch_topic_tags(slug: str) -> List[str]:
    """Return tags for one problem. Failures are transient and never cached."""
    if not slug:
        return []
    if slug in _TAG_CACHE:
        return _TAG_CACHE[slug]

    try:
        async with httpx.AsyncClient(timeout=min(settings.request_timeout, settings.topic_timeout)) as client:
            response = await client.get(PROBLEM_URL.format(slug=slug), headers=HEADERS)
    except httpx.HTTPError:
        return []

    if response.status_code != 200:
        return []

    try:
        payload: Dict[str, Any] = response.json()
    except ValueError:
        return []

    results = payload.get("results") if isinstance(payload, dict) else None
    tags = results.get("tags") if isinstance(results, dict) else None
    value = tags.get("topic_tags") if isinstance(tags, dict) else None
    if not isinstance(value, list):
        return []

    cleaned = [tag for tag in value if isinstance(tag, str)]
    _TAG_CACHE[slug] = cleaned
    return cleaned


async def build_topic_analysis(all_problems: List[Dict[str, Any]]) -> List[TopicCount]:
    slugs = sorted({p.get("slug") for p in all_problems if p.get("slug")})
    if not slugs:
        return []

    semaphore = asyncio.Semaphore(_CONCURRENCY)

    async def _bounded_fetch(slug: str) -> List[str]:
        async with semaphore:
            return await _fetch_topic_tags(slug)

    tasks = [asyncio.ensure_future(_bounded_fetch(slug)) for slug in slugs]
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks), timeout=max(0.05, float(settings.topic_timeout))
        )
    except (asyncio.TimeoutError, asyncio.CancelledError):
        # Drop queued lookups too; a cancelled request must not leave work behind.
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        return []

    counts: Dict[str, int] = {}
    for tags in results:
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1

    return [
        TopicCount(topic=topic, count=count)
        for topic, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


__all__ = ["build_topic_analysis"]
