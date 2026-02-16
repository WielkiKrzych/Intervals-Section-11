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
    if not athlete_id:
        raise ValueError("ATHLETE_ID cannot be empty")
    if not re.match(r"^[a-zA-Z0-9\-_]+$", athlete_id):
        raise ValueError("ATHLETE_ID contains invalid characters")
    return athlete_id


def get_config() -> dict[str, Any]:
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
    import base64
    credentials = base64.b64encode(f"API_KEY:{api_key}".encode()).decode()
    return {"Authorization": f"Basic {credentials}", "Accept": "application/json"}


def fetch_wellness(
    base_url: str, headers: dict[str, str], verify_ssl: bool
) -> list[dict[str, Any]]:
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


def fetch_activities(
    base_url: str, headers: dict[str, str], start: datetime, end: datetime, verify_ssl: bool
) -> list[dict[str, Any]]:
    url = f"{base_url}/events"
    params = {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")}
    try:
        response = requests.get(
            url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT, verify=verify_ssl
        )
        if response.status_code == 200:
            return response.json()
        print(f"Activities fetch failed: {response.status_code}")
        return []
    except requests.RequestException as e:
        print(f"Error fetching activities: {e}")
        return []


def fetch_profile(
    base_url: str, headers: dict[str, str], verify_ssl: bool
) -> dict[str, Any]:
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


def filter_recent_wellness(wellness: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [w for w in wellness if w.get("id", "") >= cutoff]


def compute_weekly_summary(wellness: list[dict[str, Any]]) -> dict[str, Any]:
    if not wellness:
        return {"ctl": 0, "atl": 0, "tsb": 0, "ramp_rate": 0}
    
    latest = sorted(wellness, key=lambda x: x.get("id", ""), reverse=True)[0]
    ctl = latest.get("ctl", 0) or 0
    atl = latest.get("atl", 0) or 0
    return {
        "ctl": round(ctl, 1),
        "atl": round(atl, 1),
        "tsb": round(ctl - atl, 1),
        "ramp_rate": round(latest.get("rampRate", 0) or 0, 2),
    }


def compute_sport_totals(activities: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {"Ride": {}, "Run": {}, "Swim": {}}
    
    for activity in activities:
        sport = activity.get("type", "Other")
        if sport not in totals:
            totals[sport] = {}
        
        sport_data = totals[sport]
        sport_data["total_time"] = sport_data.get("total_time", 0) + (activity.get("moving_time", 0) or 0)
        sport_data["total_kj"] = sport_data.get("total_kj", 0) + (activity.get("joules", 0) or 0) / 1000
        sport_data["total_distance"] = sport_data.get("total_distance", 0) + (activity.get("distance", 0) or 0)
        sport_data["total_load"] = sport_data.get("total_load", 0) + (activity.get("icu_training_load", 0) or 0)
    
    for sport in totals:
        if totals[sport]:
            totals[sport]["total_time_hours"] = round(totals[sport].get("total_time", 0) / 3600, 2)
            totals[sport]["total_kj"] = round(totals[sport].get("total_kj", 0), 1)
            totals[sport]["total_distance_km"] = round(totals[sport].get("total_distance", 0) / 1000, 1)
    
    return {k: v for k, v in totals.items() if v}


def compute_zone_distribution(activities: list[dict[str, Any]]) -> dict[str, int]:
    zones = {}
    for activity in activities:
        workout_doc = activity.get("workout_doc", {})
        zone_times = workout_doc.get("zoneTimes", [])
        for zone in zone_times:
            zone_name = zone.get("name", f"Z{zone.get('zone', 0)}")
            zones[zone_name] = zones.get(zone_name, 0) + zone.get("secs", 0)
    
    zone_order = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7"]
    sorted_zones = {}
    for z in zone_order:
        if z in zones:
            sorted_zones[z] = zones[z]
    sorted_zones.update({k: v for k, v in zones.items() if k not in zone_order})
    return sorted_zones


def calculate_stats(activities: list[dict[str, Any]], period_days: int) -> dict[str, Any]:
    if not activities:
        return {
            "total_activities": 0,
            "total_tss": 0,
            "total_duration_hours": 0,
            "total_energy_kj": 0,
            "period_days": period_days,
        }

    total_tss = sum(a.get("icu_training_load", 0) or 0 for a in activities)
    total_duration = sum(a.get("moving_time", 0) or 0 for a in activities)
    total_kj = sum((a.get("joules", 0) or 0) / 1000 for a in activities)

    return {
        "total_activities": len(activities),
        "total_tss": round(total_tss, 1),
        "total_duration_hours": round(total_duration / 3600, 2),
        "total_energy_kj": round(total_kj, 1),
        "period_days": period_days,
    }


def fetch_intervals_data() -> dict[str, Any]:
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

    wellness = fetch_wellness(base_url, headers, verify_ssl)
    data["wellness"] = filter_recent_wellness(wellness, days)
    data["weekly_summary"] = compute_weekly_summary(data["wellness"])
    
    activities = fetch_activities(base_url, headers, start_date, end_date, verify_ssl)
    data["activities"] = activities
    data["profile"] = fetch_profile(base_url, headers, verify_ssl)
    data["quick_stats"] = calculate_stats(activities, days)
    data["sport_totals"] = compute_sport_totals(activities)
    data["zone_distribution"] = compute_zone_distribution(activities)

    return data


def main() -> None:
    print(f"Starting sync at {datetime.now().isoformat()}")

    try:
        data = fetch_intervals_data()
        config = get_config()

        with open(config["output_path"], "w") as f:
            json.dump(data, f, indent=2)

        stats = data["quick_stats"]
        summary = data["weekly_summary"]
        print(f"✓ Sync complete. {stats['total_activities']} activities synced.")
        print(f"  TSS: {stats['total_tss']}, Duration: {stats['total_duration_hours']}h")
        print(f"  Fitness (CTL): {summary['ctl']}, Fatigue (ATL): {summary['atl']}, Form (TSB): {summary['tsb']}")

    except Exception as e:
        print(f"✗ Sync failed: {e}")
        raise


if __name__ == "__main__":
    main()
