"""Builds the unified cross-platform card for GeeksforGeeks.

Profile + difficulty breakdown come from ``get_detailed_user_data`` and the
heatmap from ``get_user_heatmap`` (active-day list, with computed streaks).
GeeksforGeeks exposes no contests, rating, badges or per-topic tags publicly, so
those sections stay empty. See ../UNIFIED_SCHEMA.md.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from math import ceil
from typing import Any, Dict, Optional

from models.unified import (
    HeatDay,
    UnifiedBadges,
    UnifiedCard,
    UnifiedContests,
    UnifiedHeatmap,
    UnifiedProfile,
    UnifiedRating,
    UnifiedStats,
    UnifiedSummary,
    YearContribution,
)
from services.gfg_service import get_detailed_user_data, get_user_heatmap

STANDARD_DIFFICULTIES = ["school", "basic", "easy", "medium", "hard"]


def profile_from(detailed: Dict[str, Any], username: str) -> UnifiedProfile:
    info = detailed.get("info", {})
    return UnifiedProfile(
        displayName=info.get("fullName") or None,
        username=info.get("userName") or username,
        avatar=info.get("profilePicture") or None,
        institution=info.get("institute") or None,
        verified=False,
    )


def stats_from(detailed: Dict[str, Any]) -> UnifiedStats:
    info = detailed.get("info", {})
    solved_stats = detailed.get("solvedStats", {})
    by_difficulty = {
        difficulty: int(solved_stats.get(difficulty, {}).get("count", 0) or 0)
        for difficulty in STANDARD_DIFFICULTIES
    }
    return UnifiedStats(
        totalSolved=int(info.get("totalProblemsSolved", 0) or 0),
        byDifficulty=by_difficulty,
        topicAnalysis=[],
    )


def _level(count: int, max_daily: int) -> int:
    if count <= 0 or max_daily <= 0:
        return 0
    return min(4, max(1, ceil((count / max_daily) * 4)))


def heatmap_from(heatmap_data: Dict[str, Any]) -> UnifiedHeatmap:
    entries = heatmap_data.get("heatmap", []) or []
    date_counts: dict[date, int] = {}
    for entry in entries:
        try:
            day = datetime.fromisoformat(str(entry.get("date"))).date()
        except (ValueError, TypeError):
            continue
        date_counts[day] = date_counts.get(day, 0) + int(entry.get("count", 0) or 0)

    if not date_counts:
        return UnifiedHeatmap(
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

    return UnifiedHeatmap(
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


def summary_from(card: UnifiedCard) -> UnifiedSummary:
    return UnifiedSummary(
        totalSolved=card.stats.totalSolved,
        totalActiveDays=card.heatmap.totalActiveDays,
        totalContests=0,
        badgesCount=0,
    )


async def build_card(username: str) -> UnifiedCard:
    detailed, heatmap_data = await asyncio.gather(
        get_detailed_user_data(username),
        get_user_heatmap(username, range_name="all"),
    )
    return UnifiedCard(
        username=username,
        profile=profile_from(detailed, username),
        stats=stats_from(detailed),
        contests=UnifiedContests(),
        rating=UnifiedRating(),
        heatmap=heatmap_from(heatmap_data),
        badges=UnifiedBadges(),
    )
