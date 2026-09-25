"""Jinko client for ground transport and lodging search (TASK T11).

Facts from the Jinko docs (https://docs.gojinko.com/llms.txt), verify on first call:
  - base URL (sandbox): https://api.sandbox.gojinko.com, auth "Authorization: Bearer jnk_..."
  - POST /v1/ground_search: rail / coach / ferry; station codes are ISO country + city (e.g. GBLON);
    results carry departure_time, arrival_time, duration_minutes
  - POST /v1/hotel_search: dates, adults, rooms, optional facility_ids; hotel prices are in major units
  - accessibility exists only as free-text facilities (hotel details), never as a boolean

Modes (env JINKO_MODE):
  live    call the API and save each raw response under data/<event>/jinko_cache/
  replay  read only from the cache (default for demos and tests; no network, no credit)
"""
from __future__ import annotations

import os
from typing import Any

JINKO_MODE = os.environ.get("JINKO_MODE", "replay")


def ground_search(origin: str, destination: str, depart_after: str, passengers: int,
                  event_id: str) -> list[dict[str, Any]]:
    """Return normalized transport results: depart, arrive, changes, overnight, price_cents (T11)."""
    raise NotImplementedError("TASK T11")


def hotel_search(destination: str, checkin: str, checkout: str, guests: int, rooms: int,
                 event_id: str) -> list[dict[str, Any]]:
    """Return normalized lodging results: name, rooms, capacity, walk_minutes,
    price_per_night_cents, step_free_hint (T11)."""
    raise NotImplementedError("TASK T11")
