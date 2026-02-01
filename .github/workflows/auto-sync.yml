#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin


def fetch_intervals_data():
    athlete_id = os.environ.get("ATHLETE_ID")
    api_key = os.environ.get("INTERVALS_KEY")

    if not athlete_id or not api_key:
        raise ValueError("Missing ATHLETE_ID or INTERVALS_KEY environment variables")

    base_url = f"https://intervals.icu/api/v1/athlete/{athlete_id}"

    end_date = datetime.now()
    start_date = end_date - timedelta(days=14)

    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

    data = {
        "athlete_id": athlete_id,
        "last_updated": datetime.now().isoformat(),
        "date_range": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        },
    }

    try:
        wellness_url = urljoin(base_url + "/", "wellness")
        wellness_response = requests.get(wellness_url, headers=headers, timeout=30)
        if wellness_response.status_code == 200:
            data["wellness"] = wellness_response.json()
        else:
            print(f"Wellness fetch failed: {wellness_response.status_code}")
            data["wellness"] = []
    except Exception as e:
        print(f"Error fetching wellness: {e}")
        data["wellness"] = []

    try:
        events_url = urljoin(base_url + "/", "events")
        params = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
        }
        events_response = requests.get(
            events_url, headers=headers, params=params, timeout=30
        )
        if events_response.status_code == 200:
            events = events_response.json()
            anonymized_events = []
            for i, event in enumerate(events):
                anon_event = event.copy()
                if (
                    "zwift" in event.get("name", "").lower()
                    or "trainer" in event.get("name", "").lower()
                ):
                    pass
                else:
                    anon_event["name"] = f"Training Session"
                anon_event["id"] = f"activity_{i + 1}"
                anonymized_events.append(anon_event)
            data["activities"] = anonymized_events
        else:
            print(f"Events fetch failed: {events_response.status_code}")
            data["activities"] = []
    except Exception as e:
        print(f"Error fetching events: {e}")
        data["activities"] = []

    try:
        profile_url = urljoin(base_url + "/", "profile")
        profile_response = requests.get(profile_url, headers=headers, timeout=30)
        if profile_response.status_code == 200:
            profile = profile_response.json()
            if "id" in profile:
                profile["id"] = "REDACTED"
            data["profile"] = profile
        else:
            print(f"Profile fetch failed: {profile_response.status_code}")
            data["profile"] = {}
    except Exception as e:
        print(f"Error fetching profile: {e}")
        data["profile"] = {}

    activities = data.get("activities", [])
    if activities:
        total_tss = sum(a.get("tss", 0) for a in activities if a.get("tss"))
        total_duration = sum(
            a.get("moving_time", 0) for a in activities if a.get("moving_time")
        )
        total_kj = sum(
            a.get("kilojoules", 0) for a in activities if a.get("kilojoules")
        )

        data["quick_stats"] = {
            "total_activities": len(activities),
            "total_tss": round(total_tss, 1),
            "total_duration_hours": round(total_duration / 3600, 2),
            "total_energy_kj": round(total_kj, 1),
            "period_days": 14,
        }
    else:
        data["quick_stats"] = {
            "total_activities": 0,
            "total_tss": 0,
            "total_duration_hours": 0,
            "total_energy_kj": 0,
            "period_days": 14,
        }

    return data


def main():
    print(f"Starting sync at {datetime.now().isoformat()}")

    try:
        data = fetch_intervals_data()

        with open("latest.json", "w") as f:
            json.dump(data, f, indent=2)

        print(
            f"✓ Sync complete. {data['quick_stats']['total_activities']} activities synced."
        )
        print(f"  TSS: {data['quick_stats']['total_tss']}")
        print(f"  Duration: {data['quick_stats']['total_duration_hours']}h")

    except Exception as e:
        print(f"✗ Sync failed: {e}")
        raise


if __name__ == "__main__":
    main()
