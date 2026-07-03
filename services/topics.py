"""Per-problem topic tag lookup for GFG solved problems.

GFG's solved-problem list (``services/profile.py::get_detailed_user_data``)
gives a slug per problem but no topic tags. Each problem's tags are fetched
individually from GFG's practice API and tallied into a topic breakdown. See
../CANONICAL_SCHEMA.md.
"""

import asyncio
from typing import Any, Dict, List

import httpx

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

_CONCURRENCY = 10


async def _fetch_topic_tags(slug: str) -> List[str]:
    if not slug:
        return []
    if slug in _TAG_CACHE:
        return _TAG_CACHE[slug]

    tags: List[str] = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(PROBLEM_URL.format(slug=slug), headers=HEADERS)
        if response.status_code == 200:
            payload: Dict[str, Any] = response.json()
            tags = list(payload.get("results", {}).get("tags", {}).get("topic_tags", []) or [])
    except (httpx.HTTPError, ValueError):
        tags = []

    _TAG_CACHE[slug] = tags
    return tags


async def build_topic_analysis(all_problems: List[Dict[str, Any]]) -> List[TopicCount]:
    slugs = sorted({p.get("slug") for p in all_problems if p.get("slug")})
    if not slugs:
        return []

    semaphore = asyncio.Semaphore(_CONCURRENCY)

    async def _bounded_fetch(slug: str) -> List[str]:
        async with semaphore:
            return await _fetch_topic_tags(slug)

    results = await asyncio.gather(*(_bounded_fetch(slug) for slug in slugs))

    counts: Dict[str, int] = {}
    for tags in results:
        for tag in tags:
            counts[tag] = counts.get(tag, 0) + 1

    return [
        TopicCount(topic=topic, count=count)
        for topic, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    ]


__all__ = ["build_topic_analysis"]
