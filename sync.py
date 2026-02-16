#!/usr/bin/env python3
"""Sync training data from Intervals.icu for AI coaching."""
import os
import json
import re
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests
from datetime import datetime, timedelta

DEFAULT_DAYS = 28
DEFAULT_TIMEOUT = 30
OUTPUT_FILENAME = "latest.json"


def validate_athlete_id(athlete_id: str) -> str:
    """Validate athlete ID format (alphanumeric and hyphens only)."""
    if not athlete_id:
        raise ValueError("ATHLETE_ID cannot be empty")
    if not re.match(r"^[a-zA-Z0-9\-_]+$", athlete_id):
        raise ValueError("ATHLETE_ID contains invalid characters")
    return athlete_id


def get_config() -> dict[str, Any]:
    """Load configuration from environment variables."""
    athlete_id = os.environ.get("ATHLETE_ID")
    api_key = os.environ.get("INTERVALS_KEY")
    verify_ssl = os.environ.get("VERIFY_SSL", "true").lower() == "true"
    days = int(os.environ.get("SYNC_DAYS", str(DEFAULT_DAYS)))
    output_path = os.environ.get("OUTPUT_PATH", OUTPUT_FILENAME)

    if not athlete_id or not api_key:
        raise ValueError("Missing ATHLETE_ID or INTERVALS_KEY environment variables")

    return {
        "athlete_id": validate_athlete_id(athlete_id),
        "api_key": api_key,
        "verify_ssl": verify_ssl,
        "days": days,
        "output_path": Path(output_path).resolve(),
    }


def get_headers(api_key: str) -> dict[str, str]:
    """Create authorization headers for API requests."""
    import base64
    credentials = base64.b64encode(f"API_KEY:{api_key}".encode()).decode()
    return {"Authorization": f"Basic {credentials}", "Accept": "application/json"}


def fetch_wellness(
    base_url: str, headers: dict[str, str], verify_ssl: bool
) -> list[dict[str, Any]]:
    """Fetch wellness data from Intervals.icu API."""
    url = f"{base_url}/wellness"
    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, verify=verify_ssl)
        if response.status_code == 200:
            return response.json()
        print(f"Wellness fetch failed: {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error fetching wellness: {e}")
        return []


def fetch_events(
    base_url: str, headers: dict[str, str], start: datetime, end: datetime, verify_ssl: bool
) -> list[dict[str, Any]]:
    """Fetch and anonymize activity events from Intervals.icu API."""
    url = f"{base_url}/events"
    params = {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
    try:
        response = requests.get(
            url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT, verify=verify_ssl
        )
        if response.status_code == 200:
            events = response.json()
            return _anonymize_events(events)
        print(f"Events fetch failed: {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        return []


def _anonymize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Anonymize event names and IDs for privacy."""
    anonymized = []
    for i, event in enumerate(events):
        anon_event = event.copy()
        name = event.get("name", "").lower()
        if "zwift" in name or "trainer" in name:
            anon_event["name"] = event.get("name", "Training Session")
        else:
            anon_event["name"] = "Training Session"
        anon_event["id"] = f"activity_{i + 1}"
        anonymized.append(anon_event)
    return anonymized


def fetch_profile(
    base_url: str, headers: dict[str, str], verify_ssl: bool
) -> dict[str, Any]:
    """Fetch athlete profile from Intervals.icu API."""
    url = f"{base_url}/profile"
    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT, verify=verify_ssl)
        if response.status_code == 200:
            profile = response.json()
            if "id" in profile:
                profile["id"] = "REDACTED"
            return profile
        print(f"Profile fetch failed: {response.status_code}")
        return {}
    except requests.RequestException as e:
        print(f"Error fetching profile: {e}")
        return {}


def calculate_stats(activities: list[dict[str, Any]], period_days: int) -> dict[str, Any]:
    """Calculate quick statistics from activities."""
    if not activities:
        return {
            "total_activities": 0,
            "total_tss": 0,
            "total_duration_hours": 0,
            "total_energy_kj": 0,
            "period_days": period_days,
        }

    total_tss = sum(a.get("tss", 0) for a in activities if a.get("tss"))
    total_duration = sum(a.get("moving_time", 0) for a in activities if a.get("moving_time"))
    total_kj = sum(a.get("kilojoules", 0) for a in activities if a.get("kilojoules"))

    return {
        "total_activities": len(activities),
        "total_tss": round(total_tss, 1),
        "total_duration_hours": round(total_duration / 3600, 2),
        "total_energy_kj": round(total_kj, 1),
        "period_days": period_days,
    }


def fetch_intervals_data() -> dict[str, Any]:
    """Fetch all data from Intervals.icu API."""
    config = get_config()
    athlete_id = config["athlete_id"]
    api_key = config["api_key"]
    verify_ssl = config["verify_ssl"]
    days = config["days"]

    base_url = f"https://intervals.icu/api/v1/athlete/{athlete_id}"
    headers = get_headers(api_key)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data: dict[str, Any] = {
        "athlete_id": athlete_id,
        "last_updated": datetime.now().isoformat(),
        "date_range": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
    }

    data["wellness"] = fetch_wellness(base_url, headers, verify_ssl)
    data["activities"] = fetch_events(base_url, headers, start_date, end_date, verify_ssl)
    data["profile"] = fetch_profile(base_url, headers, verify_ssl)
    data["quick_stats"] = calculate_stats(data.get("activities", []), days)

    return data


def main() -> None:
    """Main entry point for the sync script."""
    print(f"Starting sync at {datetime.now().isoformat()}")

    try:
        data = fetch_intervals_data()
        config = get_config()

        with open(config["output_path"], "w") as f:
            json.dump(data, f, indent=2)

        stats = data["quick_stats"]
        print(f"✓ Sync complete. {stats['total_activities']} activities synced.")
        print(f"  TSS: {stats['total_tss']}")
        print(f"  Duration: {stats['total_duration_hours']}h")

    except Exception as e:
        print(f"✗ Sync failed: {e}")
        raise


if __name__ == "__main__":
    main()
