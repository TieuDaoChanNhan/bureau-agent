"""Jinko client (T11): normalization and live/replay cache, without network."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from bureau.planner import jinko

WEI_HOTELS = dict(destination="Deauville", checkin="2026-10-09", checkout="2026-10-11", guests=40, rooms=20,
                  event_id="wei", station=(49.3583, 0.0858))

HOTEL_RESPONSE = {"hotels": [{
    "hotel_id": "h1", "name": "Test Hotel", "latitude": 49.3583, "longitude": 0.0858,
    "rooms": [
        {"max_occupancy": 1, "rates": [{"total_amount": 50.0, "currency": "EUR"}]},       # too small
        {"max_occupancy": 2, "rates": [
            {"total_amount": 180.0, "currency": "EUR", "taxes_breakdown": [
                {"amount": 6.6, "included": False}, {"amount": 15.0, "included": True}]},
            {"total_amount": 250.0, "currency": "EUR"}]},
    ]}]}

GROUND_RESPONSE = {"connections": [
    {"departure_time": "2026-10-09T18:10:00+02:00", "arrival_time": "2026-10-09T20:15:00+02:00",
     "transport_mode": "train", "from_amount": {"value": 2990, "currency": "EUR", "decimal_places": 2}},
    {"departure_time": "2026-10-09T23:00:00+02:00", "arrival_time": "2026-10-10T02:30:00+02:00",
     "transport_mode": "coach", "from_amount": {"value": 12.5, "currency": "EUR"}},
    {"departure_time": "2026-10-09T15:00:00+02:00", "arrival_time": "2026-10-09T17:00:00+02:00",
     "transport_mode": "train", "from_amount": {"value": 1000, "currency": "EUR", "decimal_places": 2}},
]}


def fake_post(status, payload, calls=None):
    def post(url, body, headers):
        if calls is not None:
            calls.append((url, body, headers))
        return status, payload
    return post


class JinkoReplayTests(unittest.TestCase):
    def test_replay_reads_the_recorded_response_without_network(self):
        with mock.patch.object(jinko, "_http_post", side_effect=AssertionError("network used")):
            hotels = jinko.hotel_search(**WEI_HOTELS, mode="replay")
        self.assertGreaterEqual(len(hotels), 1)
        for h in hotels:
            self.assertIsInstance(h["price_per_night_cents"], int)
            self.assertEqual(40, h["capacity"])
            self.assertFalse(h["step_free_hint"])
            self.assertFalse(h["group_block_confirmed"])
            self.assertEqual("jinko:replay", h["source"])

    def test_recorded_cache_contains_no_api_key(self):
        for path in (jinko.DATA_DIR / "wei" / "jinko_cache").glob("*.json"):
            self.assertNotIn("jnk_", path.read_text(encoding="utf-8"))

    def test_replay_without_cache_raises(self):
        with self.assertRaises(jinko.JinkoUnavailable):
            jinko.hotel_search("Nowhere", "2026-10-09", "2026-10-11", 40, 20, "wei", mode="replay")


class JinkoLiveTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.data = Path(tmp.name)
        for target, value in ((jinko, "DATA_DIR"), ):
            patcher = mock.patch.object(target, value, self.data)
            patcher.start()
            self.addCleanup(patcher.stop)
        env = mock.patch.dict("os.environ", {"JINKO_API_KEY": "jnk_test_secret"})
        env.start()
        self.addCleanup(env.stop)

    def test_hotel_prices_one_room_adds_excluded_taxes_and_scales_to_the_group(self):
        calls = []
        [hotel] = jinko.hotel_search(**WEI_HOTELS, mode="live", post=fake_post(200, HOTEL_RESPONSE, calls))
        # cheapest room for 2: 180.00 + 6.60 excluded tax = 18660 cents for 2 nights, x 20 rooms / 2 nights
        self.assertEqual(18660 * 20 // 2, hotel["price_per_night_cents"])
        self.assertEqual(0, hotel["walk_minutes"])
        self.assertEqual([{"adults": 2}], calls[0][1]["occupancies"])
        self.assertEqual({"X-API-Key": "jnk_test_secret"}, calls[0][2])
        self.assertTrue(calls[0][0].endswith("/v1/hotel_search"))

    def test_live_mode_caches_the_raw_response_for_replay(self):
        jinko.hotel_search(**WEI_HOTELS, mode="live", post=fake_post(200, HOTEL_RESPONSE))
        [path] = list((self.data / "wei" / "jinko_cache").glob("hotel_search_*.json"))
        self.assertEqual(HOTEL_RESPONSE, json.loads(path.read_text(encoding="utf-8"))["response"])
        replayed = jinko.hotel_search(**WEI_HOTELS, mode="replay")
        self.assertEqual("Test Hotel", replayed[0]["name"])

    def test_ground_results_are_normalized_to_cents_and_filtered_by_departure(self):
        results = jinko.ground_search("Paris", "Deauville", "2026-10-09T17:00:00+02:00", 40, "wei",
                                      mode="live", post=fake_post(200, GROUND_RESPONSE))
        self.assertEqual(["18:10", "23:00"], [r["depart"] for r in results])   # 15:00 is too early
        self.assertEqual([2990, 1250], [r["price_cents"] for r in results])   # minor vs major units
        self.assertEqual([False, True], [r["overnight"] for r in results])

    def test_unavailable_endpoint_raises_without_leaking_the_key(self):
        payload = {"error": {"code": "NOT_FOUND", "message": "route missing for jnk_test_secret"}}
        with self.assertRaises(jinko.JinkoUnavailable) as ctx:
            jinko.ground_search("Paris", "Deauville", "2026-10-09T17:00:00+02:00", 40, "wei",
                                mode="live", post=fake_post(404, payload))
        self.assertIn("404", str(ctx.exception))
        self.assertNotIn("jnk_test_secret", str(ctx.exception))
        self.assertFalse((self.data / "wei" / "jinko_cache").exists())


if __name__ == "__main__":
    unittest.main()
