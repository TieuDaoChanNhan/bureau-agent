"""Jinko client for ground transport and lodging search (TASK T11).

Verified against the live API on 2026-09-26 (docs: https://docs.gojinko.com/llms.txt):
  - base URL: https://api.gojinko.com (override with JINKO_BASE_URL). Our key ("jnk_t_…")
    authenticates there; https://api.sandbox.gojinko.com answers 401 for it.
  - auth header "X-API-Key: jnk_…" ("Authorization: Bearer jnk_…" also accepted)
  - POST /v1/hotel_search works: body {city_name, country_code, checkin, checkout,
    occupancies: [{adults}], currency, max_results}. `total_amount` is the whole stay for one
    room, in major units; some taxes are listed with included=false and must be added.
  - Group blocks are not bookable through the API: 10 x 4 or 20 x 2 occupancies in Deauville
    return empty_reason "no_availability_for_dates", and rates carry "FIT conditions … 5
    passengers and under". We therefore price one room and scale it; the group block itself
    must be confirmed with the hotel (lodging["group_block_confirmed"] is False).
  - POST /v1/ground_search returns 404 ("Route POST /api/v1/ground/search not found") for our
    key. ground_search() implements the documented schema but raises JinkoUnavailable on 404;
    the planner then keeps recorded transport options.
  - accessibility is only free text in hotel details, never a boolean: step_free_hint stays
    False here and step-free rooms remain an organizer-verified constraint.

Modes (env JINKO_MODE):
  live    call the API and save each raw response under data/<event>/jinko_cache/
  replay  read only from the cache (default for demos and tests; no network, no credit)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import date, datetime
from typing import Any, Callable, Optional

from ..config import DATA_DIR

JINKO_MODE = os.environ.get("JINKO_MODE", "replay")
BASE_URL = os.environ.get("JINKO_BASE_URL", "https://api.gojinko.com")
WALK_KMH = 4.5


class JinkoUnavailable(RuntimeError):
    """The endpoint cannot be used (not found, auth, or no cached response in replay mode)."""


def _cache_path(event_id: str, endpoint: str, body: dict):
    digest = hashlib.sha1(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return DATA_DIR / event_id / "jinko_cache" / f"{endpoint}_{digest}.json"


def _http_post(url: str, body: dict, headers: dict) -> tuple[int, Any]:
    import httpx  # imported lazily: replay mode and tests need no network stack
    resp = httpx.post(url, json=body, headers=headers, timeout=120)
    try:
        payload = resp.json()
    except ValueError:
        payload = {"error": resp.text[:300]}
    return resp.status_code, payload


def _call(endpoint: str, body: dict, event_id: str, mode: Optional[str] = None,
          post: Callable[[str, dict, dict], tuple[int, Any]] = _http_post) -> dict:
    """Return the raw response for `body`: from the API in live mode (and cache it), else from the cache."""
    mode = mode or JINKO_MODE
    path = _cache_path(event_id, endpoint, body)
    if mode != "live":
        if not path.exists():
            raise JinkoUnavailable(f"No cached {endpoint} response ({path.name}); run once with JINKO_MODE=live")
        return json.loads(path.read_text(encoding="utf-8"))["response"]
    key = os.environ.get("JINKO_API_KEY", "")
    if not key:
        raise JinkoUnavailable("JINKO_API_KEY is not set")
    status, payload = post(f"{BASE_URL}/v1/{endpoint}", body, {"X-API-Key": key})
    if status != 200:
        detail = json.dumps(payload, ensure_ascii=False)[:300].replace(key, "[KEY]")
        raise JinkoUnavailable(f"{endpoint} returned HTTP {status}: {detail}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"endpoint": endpoint, "request": body, "response": payload,
                                "fetched_at": datetime.now().astimezone().isoformat()},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    return payload


def _cents(major: float) -> int:
    return int(round(float(major) * 100))


def _hhmm(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%H:%M")


def ground_search(origin: str, destination: str, depart_after: str, passengers: int,
                  event_id: str, mode: Optional[str] = None, post=_http_post) -> list[dict[str, Any]]:
    """Return normalized transport results: depart, arrive, changes, overnight, price_cents (T11).

    Prices are per person (one passenger is searched). Raises JinkoUnavailable when the
    endpoint is not available for the key (HTTP 404 as of 2026-09-26) or not cached.
    """
    day = depart_after[:10]
    body = {"departure_city": origin, "arrival_city": destination, "departure_date": day,
            "passengers": [{"pax": 1}], "currency": "EUR"}
    raw = _call("ground_search", body, event_id, mode, post)
    earliest = datetime.fromisoformat(depart_after)
    out = []
    for c in raw.get("connections", []):
        dep, arr = datetime.fromisoformat(c["departure_time"]), datetime.fromisoformat(c["arrival_time"])
        if dep.tzinfo and earliest.tzinfo and dep < earliest:
            continue
        price = c.get("from_amount") or (c.get("fares") or [{}])[0].get("total_price") or {}
        value, places = price.get("value"), price.get("decimal_places")
        # Integer values with decimal_places are minor units; plain numbers are major units.
        cents = (int(value) * 10 ** (2 - places) if isinstance(value, int) and places is not None
                 else _cents(value or 0))
        out.append({"mode": c.get("transport_mode", "train"), "depart": _hhmm(c["departure_time"]),
                    "arrive": _hhmm(c["arrival_time"]), "changes": int(c.get("changes", 0)),
                    "overnight": arr.date() > dep.date(), "arrives_next_day": arr.date() > dep.date(),
                    "price_cents": cents, "source": f"jinko:{mode or JINKO_MODE}"})
    return out


def _walk_minutes(lat: Optional[float], lon: Optional[float], station: Optional[tuple[float, float]]):
    if station is None or lat is None or lon is None:
        return None
    r = 6371.0
    p1, p2 = math.radians(lat), math.radians(station[0])
    dp, dl = p2 - p1, math.radians(station[1] - lon)
    km = 2 * r * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
    return int(round(km / WALK_KMH * 60))


def hotel_search(destination: str, checkin: str, checkout: str, guests: int, rooms: int,
                 event_id: str, mode: Optional[str] = None, post=_http_post, country_code: str = "fr",
                 station: Optional[tuple[float, float]] = None, max_results: int = 10) -> list[dict[str, Any]]:
    """Return normalized lodging results: name, rooms, capacity, walk_minutes,
    price_per_night_cents, step_free_hint (T11).

    One room of ceil(guests / rooms) adults is priced (the API does not quote group blocks),
    then scaled to `rooms`. Taxes marked not included are added. `price_per_night_cents` is
    for the whole group; `group_block_confirmed` is False until organizers confirm with the hotel.
    """
    per_room = math.ceil(guests / rooms)
    body = {"city_name": destination, "country_code": country_code, "checkin": checkin, "checkout": checkout,
            "occupancies": [{"adults": per_room}], "currency": "EUR", "max_results": max_results}
    raw = _call("hotel_search", body, event_id, mode, post)
    nights = (date.fromisoformat(checkout) - date.fromisoformat(checkin)).days
    out = []
    for h in raw.get("hotels", []):
        best = None
        for room in h.get("rooms", []):
            if (room.get("max_occupancy") or per_room) < per_room:
                continue
            for rate in room.get("rates", []):
                if rate.get("currency", "EUR") != "EUR":
                    continue
                extra = sum(t["amount"] for t in rate.get("taxes_breakdown", []) if t.get("included") is False)
                stay = _cents(rate["total_amount"] + extra)
                if best is None or stay < best:
                    best = stay
        if best is None:
            continue
        out.append({"name": h["name"], "rooms": rooms, "capacity": rooms * per_room,
                    "walk_minutes": _walk_minutes(h.get("latitude"), h.get("longitude"), station),
                    "price_per_night_cents": -(-best * rooms // nights), "step_free_hint": False,
                    "group_block_confirmed": False, "hotel_id": h.get("hotel_id"),
                    "source": f"jinko:{mode or JINKO_MODE}"})
    return out
