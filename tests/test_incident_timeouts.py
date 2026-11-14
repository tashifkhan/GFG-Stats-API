"""Offline regressions for the Vercel timeout incident."""

import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
from fastapi import HTTPException

from app import app
from config import settings
from core import cache, rate_limit
from models.canonical import Card
from routes import summary
from services import client, topics


class UpstreamTests(unittest.IsolatedAsyncioTestCase):
    def mock_client(self, response=None, side_effect=None):
        mock = AsyncMock()
        mock.__aenter__.return_value = mock
        mock.request.side_effect = side_effect
        mock.request.return_value = response
        return mock

    async def test_total_deadline_cancels_a_request_even_without_httpx_timeout(self):
        cancelled = asyncio.Event()

        async def stalled(*args, **kwargs):
            try:
                await asyncio.sleep(60)
            finally:
                cancelled.set()

        with patch.object(settings, "request_timeout", 0.02), patch.object(
            client.httpx, "AsyncClient", return_value=self.mock_client(side_effect=stalled)
        ), self.assertLogs("gfg", level="WARNING") as logs:
            with self.assertRaises(HTTPException) as error:
                await client._request_json("GET", client.PROFILE_URL, params={"handle": "private-handle"})
        self.assertEqual(error.exception.status_code, 504)
        self.assertTrue(cancelled.is_set())
        self.assertIn("outcome=timeout", " ".join(logs.output))
        self.assertNotIn("private-handle", " ".join(logs.output))

    async def test_dependency_failure_cancels_siblings(self):
        running = asyncio.Event()
        cancelled = asyncio.Event()

        async def failed():
            await running.wait()
            raise HTTPException(503, "Unavailable")

        async def stalled():
            running.set()
            try:
                await asyncio.sleep(60)
            finally:
                cancelled.set()

        with self.assertRaises(HTTPException):
            await client.gather_required(failed(), stalled())
        self.assertTrue(cancelled.is_set())

    async def test_upstream_errors_are_controlled(self):
        cases = [
            (429, {"message": "Too many requests"}, 503),
            (403, {"message": "Blocked"}, 502),
            (500, {"message": "Unavailable"}, 502),
            (404, {"message": "User not found"}, 404),
            (200, [], 502),
        ]
        for upstream_status, payload, expected_status in cases:
            with self.subTest(upstream_status=upstream_status, payload=payload):
                response = httpx.Response(upstream_status, json=payload)
                with patch.object(client.httpx, "AsyncClient", return_value=self.mock_client(response)):
                    with self.assertRaises(HTTPException) as error:
                        await client._request_json("GET", client.PROFILE_URL)
                self.assertEqual(error.exception.status_code, expected_status)

    async def test_html_error_response_does_not_become_an_unhandled_exception(self):
        response = httpx.Response(503, text="<html>Unavailable</html>")
        with patch.object(client.httpx, "AsyncClient", return_value=self.mock_client(response)):
            with self.assertRaises(HTTPException) as error:
                await client._request_json("GET", client.PROFILE_URL)
        self.assertEqual(error.exception.status_code, 502)

    async def test_network_failure_returns_service_unavailable(self):
        with patch.object(client.httpx, "AsyncClient", return_value=self.mock_client(
            side_effect=httpx.ConnectError("private connection details")
        )), self.assertLogs("gfg", level="WARNING") as logs:
            with self.assertRaises(HTTPException) as error:
                await client._request_json("GET", client.PROFILE_URL)
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn("private connection details", " ".join(logs.output))


class RequestTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, path):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
            return await http.get(path, headers={"Origin": "https://example.org"})

    async def test_entire_request_deadline_cancels_route_and_preserves_cors(self):
        cancelled = asyncio.Event()

        async def stalled(username):
            try:
                await asyncio.sleep(60)
            finally:
                cancelled.set()

        with patch.object(settings, "response_timeout", 0.02), patch(
            "core.middleware.redis_enabled", return_value=False
        ), patch("routes.profile.get_detailed_user_data", side_effect=stalled), self.assertLogs("gfg") as logs:
            response = await self.request("/private-handle/profile?secret=private-value")
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["endpoint"], "profile")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["access-control-allow-origin"], "*")
        self.assertTrue(cancelled.is_set())
        self.assertIn("route=/{username}/profile", " ".join(logs.output))
        self.assertNotIn("private-handle", " ".join(logs.output))
        self.assertNotIn("private-value", " ".join(logs.output))

    async def test_deadline_includes_cache_access(self):
        async def stalled(key):
            await asyncio.sleep(60)

        with patch.object(settings, "response_timeout", 0.02), patch(
            "core.middleware.redis_enabled", return_value=True
        ), patch("core.middleware.get_json", side_effect=stalled):
            response = await self.request("/alice/profile")
        self.assertEqual(response.status_code, 504)

    async def test_profile_timeout_uses_existing_error_contract(self):
        with patch("core.middleware.redis_enabled", return_value=False), patch(
            "routes.profile.get_detailed_user_data", side_effect=HTTPException(504, "Upstream timed out")
        ):
            response = await self.request("/alice/profile")
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json(), {
            "error": True, "message": "Upstream timed out", "status_code": 504, "endpoint": "profile"
        })

    async def test_summary_reuses_card_total_without_another_upstream_fetch(self):
        card = Card(username="alice")
        card.stats.totalSolved = 42
        with patch.object(summary.canonical_mapper, "build_card", new=AsyncMock(return_value=card)):
            response = await summary.get_summary("alice")
        self.assertEqual(response["totalProblemsSolved"], 42)

    async def test_stats_remains_successful_when_optional_topic_lookup_stalls(self):
        async def stalled(slug):
            await asyncio.sleep(60)

        detailed = {
            "info": {"totalProblemsSolved": 100},
            "solvedStats": {"easy": {"count": 100}},
            "allProblems": [{"slug": str(i)} for i in range(100)],
        }
        with patch.object(settings, "topic_timeout", 0.02), patch(
            "core.middleware.redis_enabled", return_value=False
        ), patch("routes.stats.get_detailed_user_data", new=AsyncMock(return_value=detailed)), patch.object(
            topics, "_fetch_topic_tags", stalled
        ):
            response = await self.request("/alice/stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["totalSolved"], 100)
        self.assertEqual(response.json()["data"]["topicAnalysis"], [])


class OptionalDependencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_topic_fanout_has_one_budget_and_cancels_queued_work(self):
        active = set()
        started = set()

        async def stalled(slug):
            active.add(slug)
            started.add(slug)
            try:
                await asyncio.sleep(60)
            finally:
                active.remove(slug)

        with patch.object(settings, "topic_timeout", 0.02), patch.object(topics, "_fetch_topic_tags", stalled):
            result = await topics.build_topic_analysis([{"slug": str(i)} for i in range(100)])
        self.assertEqual(result, [])
        self.assertEqual(active, set())
        self.assertEqual(len(started), topics._CONCURRENCY)

    async def test_transient_topic_failure_is_not_cached(self):
        topics._TAG_CACHE.clear()
        mock = AsyncMock()
        mock.__aenter__.return_value = mock
        mock.get.side_effect = [httpx.Response(503), httpx.Response(200, json={
            "results": {"tags": {"topic_tags": ["Arrays"]}}
        })]
        with patch.object(topics.httpx, "AsyncClient", return_value=mock):
            self.assertEqual(await topics._fetch_topic_tags("example"), [])
            self.assertNotIn("example", topics._TAG_CACHE)
            self.assertEqual(await topics._fetch_topic_tags("example"), ["Arrays"])

    async def test_stalled_redis_does_not_block_cache_or_rate_limiter(self):
        async def stalled(*args, **kwargs):
            await asyncio.sleep(60)

        fake_redis = SimpleNamespace(get=stalled, setex=stalled, ttl=stalled)
        with patch.object(cache, "get_redis", return_value=fake_redis), patch.object(
            cache, "REDIS_OPERATION_TIMEOUT", 0.02
        ):
            self.assertIsNone(await cache.get_json("private-cache-key"))
            await cache.set_json("private-cache-key", {"ok": True}, 60)
        with patch.object(rate_limit, "get_redis", return_value=fake_redis), patch.object(
            rate_limit, "RATE_LIMIT_TIMEOUT", 0.02
        ):
            result = await rate_limit.check_rate_limit("private-ip-key", 60, 60, "ip")
        self.assertTrue(result.allowed)

    async def test_cached_response_skips_upstreams(self):
        cached = {
            "body": cache.encode_body(json.dumps({"status": "success"}).encode()),
            "status_code": 200, "headers": {"content-type": "application/json"},
        }
        with patch("core.middleware.redis_enabled", return_value=True), patch(
            "core.middleware.get_json", new=AsyncMock(return_value=cached)
        ), patch("routes.profile.get_detailed_user_data", new=AsyncMock()) as upstream:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
                response = await http.get("/alice/profile")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-cache"], "HIT")
        upstream.assert_not_awaited()
