"""Offline tests for GFG topic-tag aggregation (see ../CANONICAL_SCHEMA.md)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services import topics  # noqa: E402
from services.canonical_mapper import stats_from  # noqa: E402


class TopicAnalysisTests(unittest.IsolatedAsyncioTestCase):
    async def test_build_topic_analysis_tallies_and_sorts(self):
        fake_tags = {
            "kadane": ["Arrays", "Dynamic Programming"],
            "reverse-ll": ["Linked List"],
            "two-sum": ["Arrays", "Hashing"],
        }

        async def fake_fetch(slug: str):
            return fake_tags.get(slug, [])

        topics._TAG_CACHE.clear()
        original = topics._fetch_topic_tags
        topics._fetch_topic_tags = fake_fetch
        try:
            result = await topics.build_topic_analysis(
                [{"slug": "kadane"}, {"slug": "reverse-ll"}, {"slug": "two-sum"}, {"slug": "kadane"}]
            )
        finally:
            topics._fetch_topic_tags = original

        as_dict = {t.topic: t.count for t in result}
        self.assertEqual(as_dict, {"Arrays": 2, "Dynamic Programming": 1, "Linked List": 1, "Hashing": 1})
        self.assertEqual(result[0].topic, "Arrays")

    async def test_build_topic_analysis_empty_when_no_problems(self):
        result = await topics.build_topic_analysis([])
        self.assertEqual(result, [])

    async def test_stats_from_populates_topic_analysis(self):
        async def fake_build(all_problems):
            return [topics.TopicCount(topic="Arrays", count=2)]

        original = topics.build_topic_analysis
        topics.build_topic_analysis = fake_build
        try:
            stats = await stats_from(
                {
                    "info": {"totalProblemsSolved": 2},
                    "solvedStats": {},
                    "allProblems": [{"slug": "kadane"}],
                }
            )
        finally:
            topics.build_topic_analysis = original

        self.assertEqual([t.topic for t in stats.topicAnalysis], ["Arrays"])


if __name__ == "__main__":
    unittest.main()
