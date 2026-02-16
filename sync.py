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


def generate_csv(data: dict[str, Any]) -> str:
    output = []
    
    output.append("=== ACTIVITIES ===")
    output.append("date,type,name,duration_min,tss,kj,distance_km")
    for a in data.get("activities", []):
        date = a.get("start_date_local", "")[:10]
        type_ = a.get("type", "")
        name = a.get("name", "").replace(",", ";")
        duration = (a.get("moving_time", 0) or 0) // 60
        tss = a.get("icu_training_load", 0) or 0
        kj = (a.get("joules", 0) or 0) / 1000
        dist = (a.get("distance", 0) or 0) / 1000
        output.append(f"{date},{type_},{name},{duration},{tss},{kj:.1f},{dist:.1f}")
    
    output.append("")
    output.append("=== WELLNESS ===")
    output.append("date,sleep_hrs,resting_hr,hrv,weight,readiness,soreness,fatigue,steps,ctl,atl,tsb")
    for w in data.get("wellness", []):
        date = w.get("id", "")
        sleep = (w.get("sleepSecs", 0) or 0) / 3600
        resting_hr = w.get("restingHR", "") or ""
        hrv = w.get("hrv", "") or ""
        weight = w.get("weight", "") or ""
        readiness = w.get("readiness", "") or ""
        soreness = w.get("soreness", "") or ""
        fatigue = w.get("fatigue", "") or ""
        steps = w.get("steps", "") or ""
        ctl = w.get("ctl", "") or ""
        atl = w.get("atl", "") or ""
        tsb = round((ctl or 0) - (atl or 0), 1) if ctl and atl else ""
        output.append(f"{date},{sleep:.1f},{resting_hr},{hrv},{weight},{readiness},{soreness},{fatigue},{steps},{ctl},{atl},{tsb}")
    
    output.append("")
    output.append("=== SPORT TOTALS ===")
    for sport, totals in data.get("sport_totals", {}).items():
        output.append(f"{sport},{totals.get('total_time_hours', 0)}h,{totals.get('total_kj', 0)}kJ,{totals.get('total_distance_km', 0)}km,{totals.get('total_load', 0)} TSS")
    
    return "\n".join(output)


def generate_html_report(data: dict[str, Any]) -> str:
    stats = data["quick_stats"]
    summary = data["weekly_summary"]
    sport_totals = data.get("sport_totals", {})
    zones = data.get("zone_distribution", {})
    wellness = data.get("wellness", [])
    
    latest_wellness = sorted(wellness, key=lambda x: x.get("id", ""), reverse=True)[0] if wellness else {}
    
    zone_data = []
    zone_labels = []
    total_zones = sum(zones.values())
    for zone, secs in zones.items():
        if secs > 0:
            zone_labels.append(f"'{zone}'")
            zone_data.append(str(round(secs / 60)))
    
    wellness_sorted = sorted(wellness, key=lambda x: x.get("id", ""))
    wellness_dates = [w.get("id", "") for w in wellness_sorted][-14:]
    ctl_data = [w.get("ctl", 0) or 0 for w in wellness_sorted][-14:]
    atl_data = [w.get("atl", 0) or 0 for w in wellness_sorted][-14:]
    
    sport_rows = "".join(f"<tr><td>{sport}</td><td>{t.get('total_time_hours', 0)}h</td><td>{t.get('total_distance_km', 0)} km</td><td>{t.get('total_kj', 0)} kJ</td><td>{t.get('total_load', 0)}</td></tr>" for sport, t in sport_totals.items())
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Training Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f7;
            --text-primary: #1d1d1f;
            --text-secondary: #86868b;
            --accent: #0071e3;
            --card-bg: #ffffff;
            --shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-primary: #1d1d1f;
                --bg-secondary: #2c2c2e;
                --text-primary: #f5f5f7;
                --text-secondary: #98989d;
                --accent: #0a84ff;
                --card-bg: #2c2c2e;
                --shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-secondary); color: var(--text-primary); padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
        h2 {{ font-size: 1.25rem; margin: 1.5rem 0 1rem; color: var(--text-secondary); }}
        h3 {{ font-size: 1rem; margin-bottom: 0.5rem; }}
        .subtitle {{ color: var(--text-secondary); margin-bottom: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 1rem; }}
        .card {{ background: var(--card-bg); border-radius: 12px; padding: 20px; box-shadow: var(--shadow); }}
        .metric {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--bg-secondary); }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: var(--text-secondary); font-size: 0.9rem; }}
        .metric-value {{ font-weight: 600; font-size: 1.1rem; }}
        .status-ok {{ color: #34c759; }}
        .status-warning {{ color: #ff9500; }}
        .status-danger {{ color: #ff3b30; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid var(--bg-secondary); }}
        th {{ color: var(--text-secondary); font-weight: 500; font-size: 0.85rem; }}
        .chart-container {{ position: relative; height: 250px; }}
        .footer {{ text-align: center; color: var(--text-secondary); margin-top: 2rem; font-size: 0.85rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Training Report</h1>
        <p class="subtitle">{data['date_range']['start']} to {data['date_range']['end']}</p>
        
        <div class="grid">
            <div class="card">
                <h2>Training Status</h2>
                <div class="metric">
                    <span class="metric-label">Fitness (CTL)</span>
                    <span class="metric-value">{summary['ctl']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Fatigue (ATL)</span>
                    <span class="metric-value">{summary['atl']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Form (TSB)</span>
                    <span class="metric-value {'status-ok' if summary['tsb'] > 0 else 'status-warning'}">{summary['tsb']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Ramp Rate</span>
                    <span class="metric-value">{summary['ramp_rate']}</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Activity Summary</h2>
                <div class="metric">
                    <span class="metric-label">Activities</span>
                    <span class="metric-value">{stats['total_activities']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Duration</span>
                    <span class="metric-value">{stats['total_duration_hours']}h</span>
                </div>
                <div class="metric">
                    <span class="metric-label">TSS</span>
                    <span class="metric-value">{stats['total_tss']}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Energy</span>
                    <span class="metric-value">{stats['total_energy_kj']} kJ</span>
                </div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Performance Chart (CTL vs ATL)</h2>
                <div class="chart-container">
                    <canvas id="fitnessChart"></canvas>
                </div>
            </div>
            <div class="card">
                <h2>Zone Distribution</h2>
                <div class="chart-container">
                    <canvas id="zoneChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Sport Breakdown</h2>
            <table>
                <thead>
                    <tr><th>Sport</th><th>Time</th><th>Distance</th><th>Energy</th><th>Load</th></tr>
                </thead>
                <tbody>
                    {sport_rows}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>Latest Wellness</h2>
            <div class="grid">
                <div>
                    <div class="metric"><span class="metric-label">Sleep</span><span class="metric-value">{latest_wellness.get('sleepSecs', 0) / 3600:.1f}h</span></div>
                    <div class="metric"><span class="metric-label">Resting HR</span><span class="metric-value">{latest_wellness.get('restingHR', '-')} bpm</span></div>
                    <div class="metric"><span class="metric-label">HRV</span><span class="metric-value">{latest_wellness.get('hrv', '-')}</span></div>
                </div>
                <div>
                    <div class="metric"><span class="metric-label">Weight</span><span class="metric-value">{latest_wellness.get('weight', '-')} kg</span></div>
                    <div class="metric"><span class="metric-label">Readiness</span><span class="metric-value">{latest_wellness.get('readiness', '-')}%</span></div>
                    <div class="metric"><span class="metric-label">Steps</span><span class="metric-value">{latest_wellness.get('steps', '-')}</span></div>
                </div>
            </div>
        </div>
        
        <p class="footer">Last updated: {data['last_updated']}</p>
    </div>
    
    <script>
        new Chart(document.getElementById('fitnessChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(wellness_dates)},
                datasets: [{{
                    label: 'CTL (Fitness)',
                    data: {json.dumps(ctl_data)},
                    borderColor: '#34c759',
                    backgroundColor: 'rgba(52, 199, 89, 0.1)',
                    fill: true
                }}, {{
                    label: 'ATL (Fatigue)',
                    data: {json.dumps(atl_data)},
                    borderColor: '#ff9500',
                    backgroundColor: 'rgba(255, 149, 0, 0.1)',
                    fill: true
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});
        
        new Chart(document.getElementById('zoneChart'), {{
            type: 'pie',
            data: {{
                labels: {json.dumps(zone_labels)},
                datasets: [{{ data: {json.dumps(zone_data)} }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});
    </script>
</body>
</html>"""


def generate_markdown_report(data: dict[str, Any]) -> str:
    stats = data["quick_stats"]
    summary = data["weekly_summary"]
    sport_totals = data.get("sport_totals", {})
    zones = data.get("zone_distribution", {})
    wellness = data.get("wellness", [])
    
    latest_wellness = sorted(wellness, key=lambda x: x.get("id", ""), reverse=True)[0] if wellness else {}
    
    lines = [
        f"# Training Report",
        f"**Period:** {data['date_range']['start']} to {data['date_range']['end']}",
        f"**Last Updated:** {data['last_updated']}",
        "",
        "## Training Status",
        f"- **Fitness (CTL):** {summary['ctl']} - Chronic Training Load",
        f"- **Fatigue (ATL):** {summary['atl']} - Acute Training Load", 
        f"- **Form (TSB):** {summary['tsb']} = CTL - ATL (negative = overtraining)",
        f"- **Ramp Rate:** {summary['ramp_rate']}",
        "",
        "## Activity Summary",
        f"- **Total Activities:** {stats['total_activities']}",
        f"- **Total Duration:** {stats['total_duration_hours']}h",
        f"- **Total TSS:** {stats['total_tss']}",
        f"- **Total Energy:** {stats['total_energy_kj']} kJ",
        "",
    ]
    
    if sport_totals:
        lines.append("## Sport Breakdown")
        for sport, totals in sport_totals.items():
            lines.append(f"### {sport}")
            lines.append(f"- Time: {totals.get('total_time_hours', 0)}h")
            if totals.get('total_distance_km'):
                lines.append(f"- Distance: {totals['total_distance_km']} km")
            if totals.get('total_kj'):
                lines.append(f"- Energy: {totals['total_kj']} kJ")
            if totals.get('total_load'):
                lines.append(f"- Load: {totals['total_load']}")
            lines.append("")
    
    if zones:
        lines.append("## Zone Distribution")
        total_secs = sum(zones.values())
        for zone, secs in zones.items():
            if secs > 0:
                pct = (secs / total_secs * 100) if total_secs > 0 else 0
                mins = secs // 60
                lines.append(f"- **{zone}:** {mins}m ({pct:.1f}%)")
        lines.append("")
    
    if latest_wellness:
        lines.append("## Daily Wellness (Latest)")
        w = latest_wellness
        if w.get('sleepSecs'):
            sleep_hours = w['sleepSecs'] / 3600
            lines.append(f"- **Sleep:** {sleep_hours:.1f}h")
        if w.get('restingHR'):
            lines.append(f"- **Resting HR:** {w['restingHR']} bpm")
        if w.get('hrv'):
            lines.append(f"- **HRV:** {w['hrv']}")
        if w.get('weight'):
            lines.append(f"- **Weight:** {w['weight']} kg")
        if w.get('readiness'):
            lines.append(f"- **Readiness:** {w['readiness']}%")
        if w.get('soreness'):
            lines.append(f"- **Soreness:** {w['soreness']}/5")
        if w.get('fatigue'):
            lines.append(f"- **Fatigue:** {w['fatigue']}/5")
        if w.get('steps'):
            lines.append(f"- **Steps:** {w['steps']}")
        lines.append("")
    
    return "\n".join(lines)


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
        output_dir = config["output_path"].parent

        json_path = config["output_path"]
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

        md_path = output_dir / "latest.md"
        with open(md_path, "w") as f:
            f.write(generate_markdown_report(data))

        csv_path = output_dir / "latest.csv"
        with open(csv_path, "w") as f:
            f.write(generate_csv(data))

        html_path = output_dir / "latest.html"
        with open(html_path, "w") as f:
            f.write(generate_html_report(data))

        stats = data["quick_stats"]
        summary = data["weekly_summary"]
        print(f"✓ Sync complete. {stats['total_activities']} activities synced.")
        print(f"  TSS: {stats['total_tss']}, Duration: {stats['total_duration_hours']}h")
        print(f"  Fitness (CTL): {summary['ctl']}, Fatigue (ATL): {summary['atl']}, Form (TSB): {summary['tsb']}")
        print(f"  Reports saved:")
        print(f"    - JSON: {json_path}")
        print(f"    - Markdown: {md_path}")
        print(f"    - CSV: {csv_path}")
        print(f"    - HTML: {html_path}")

    except Exception as e:
        print(f"✗ Sync failed: {e}")
        raise


if __name__ == "__main__":
    main()
