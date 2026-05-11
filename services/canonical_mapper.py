"""Builds the canonical cross-platform card for GeeksforGeeks.

Profile + difficulty breakdown come from ``get_detailed_user_data`` and the
heatmap from ``get_user_heatmap`` (active-day list, with computed streaks).
GeeksforGeeks exposes no contests, rating, badges or per-topic tags publicly, so
those sections stay empty. See ../CANONICAL_SCHEMA.md.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from math import ceil
from typing import Any, Dict, Optional

from models.canonical.badges import Badges
from models.canonical.card import Card
from models.canonical.contests import Contests
from models.canonical.heatmap import HeatDay, Heatmap, YearContribution
from models.canonical.profile import Profile
from models.canonical.rating import Rating
from models.canonical.stats import Stats
from models.canonical.summary import Summary
from services import topics
from services.heatmap import get_user_heatmap
from services.heatmap_window import window_heatmap
from services.profile import get_detailed_user_data

STANDARD_DIFFICULTIES = ["school", "basic", "easy", "medium", "hard"]


def profile_from(detailed: Dict[str, Any], username: str) -> Profile:
    info = detailed.get("info", {})
    return Profile(
        displayName=info.get("fullName") or None,
        username=info.get("userName") or username,
        avatar=info.get("profilePicture") or None,
        institution=info.get("institute") or None,
        verified=False,
    )


async def stats_from(detailed: Dict[str, Any]) -> Stats:
    info = detailed.get("info", {})
    solved_stats = detailed.get("solvedStats", {})
    by_difficulty = {
        difficulty: int(solved_stats.get(difficulty, {}).get("count", 0) or 0)
        for difficulty in STANDARD_DIFFICULTIES
    }
    return Stats(
        totalSolved=int(info.get("totalProblemsSolved", 0) or 0),
        byDifficulty=by_difficulty,
        topicAnalysis=await topics.build_topic_analysis(detailed.get("allProblems", [])),
    )


def _level(count: int, max_daily: int) -> int:
    if count <= 0 or max_daily <= 0:
        return 0
    return min(4, max(1, ceil((count / max_daily) * 4)))


def heatmap_from(heatmap_data: Dict[str, Any]) -> Heatmap:
    entries = heatmap_data.get("heatmap", []) or []
    date_counts: dict[date, int] = {}
    for entry in entries:
        try:
            day = datetime.fromisoformat(str(entry.get("date"))).date()
        except (ValueError, TypeError):
            continue
        date_counts[day] = date_counts.get(day, 0) + int(entry.get("count", 0) or 0)

    if not date_counts:
        return Heatmap(
            totalActiveDays=int(heatmap_data.get("totalActiveDays", 0) or 0),
            totalSubmissions=int(heatmap_data.get("totalSubmissions", 0) or 0),
        )

    active_dates = sorted(date_counts)
    max_daily = max(date_counts.values())

    longest = current = 1
    for i in range(1, len(active_dates)):
        if active_dates[i] - active_dates[i - 1] == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    today = datetime.now(timezone.utc).date()
    cursor = (
        today
        if date_counts.get(today, 0) > 0
        else (
            today - timedelta(days=1)
            if date_counts.get(today - timedelta(days=1), 0) > 0
            else None
        )
    )
    current_streak = 0
    while cursor is not None and date_counts.get(cursor, 0) > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    yearly: dict[int, dict] = {}
    for day, count in date_counts.items():
        bucket = yearly.setdefault(day.year, {"totalSubmissions": 0, "activeDays": 0})
        bucket["totalSubmissions"] += count
        bucket["activeDays"] += 1

    return Heatmap(
        totalSubmissions=sum(date_counts.values()),
        totalActiveDays=len(active_dates),
        currentStreak=current_streak,
        longestStreak=longest,
        maxDailySubmissions=max_daily,
        firstActiveDate=active_dates[0].isoformat(),
        lastActiveDate=active_dates[-1].isoformat(),
        dailyContributions=[
            HeatDay(
                date=d.isoformat(),
                count=date_counts[d],
                level=_level(date_counts[d], max_daily),
            )
            for d in active_dates
        ],
        yearlyContributions=[
            YearContribution(
                year=y,
                totalSubmissions=v["totalSubmissions"],
                activeDays=v["activeDays"],
            )
            for y, v in sorted(yearly.items())
        ],
    )


def summary_from(card: Card) -> Summary:
    return Summary(
        totalSolved=card.stats.totalSolved,
        totalActiveDays=card.heatmap.totalActiveDays,
        totalContests=0,
        badgesCount=0,
    )


async def build_card(username: str) -> Card:
    detailed, heatmap_data = await asyncio.gather(
        get_detailed_user_data(username),
        get_user_heatmap(username, range_name="all"),
    )
    available_years = [int(y) for y in (heatmap_data.get("availableYears") or [])]
    return Card(
        username=username,
        profile=profile_from(detailed, username),
        stats=await stats_from(detailed),
        contests=Contests(),
        rating=Rating(),
        heatmap=window_heatmap(heatmap_from(heatmap_data), "all", None, available_years=available_years or None),
        badges=Badges(),
    )
