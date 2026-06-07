"""
Strava Sync Script — Fetches running activities and writes data/activities.json.
Runs as a GitHub Action on a daily schedule.

Required environment variables (set as GitHub Secrets):
  STRAVA_CLIENT_ID     — from https://www.strava.com/settings/api
  STRAVA_CLIENT_SECRET — from https://www.strava.com/settings/api
  STRAVA_REFRESH_TOKEN — obtained during initial OAuth setup
"""

import os
import json
import requests
from datetime import datetime, timedelta

STRAVA_API = "https://www.strava.com/api/v3"

def get_access_token():
    """Exchange refresh token for a fresh access token."""
    resp = requests.post(f"{STRAVA_API}/oauth/token", data={
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    })
    resp.raise_for_status()
    data = resp.json()

    # Save new refresh token if rotated
    new_refresh = data.get("refresh_token")
    if new_refresh and new_refresh != os.environ["STRAVA_REFRESH_TOKEN"]:
        print(f"::warning::Strava rotated your refresh token. Update the STRAVA_REFRESH_TOKEN secret.")
        # Write to GitHub output so the workflow can update if needed
        gh_output = os.environ.get("GITHUB_OUTPUT")
        if gh_output:
            with open(gh_output, "a") as f:
                f.write(f"new_refresh_token={new_refresh}\n")

    return data["access_token"]


def fetch_activities(token, per_page=200, max_pages=10):
    """Fetch all running activities from Strava."""
    all_activities = []
    page = 1
    while page <= max_pages:
        resp = requests.get(f"{STRAVA_API}/athlete/activities", headers={
            "Authorization": f"Bearer {token}",
        }, params={
            "per_page": per_page,
            "page": page,
        })
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_activities.extend(batch)
        page += 1
    return all_activities


def process_activities(raw):
    """Filter for runs and format for the dashboard."""
    runs = [a for a in raw if a.get("type") == "Run" or a.get("sport_type") == "Run"]

    activities = []
    for a in runs:
        dist_m = a.get("distance", 0)
        elapsed = a.get("elapsed_time", 0)
        moving = a.get("moving_time", 0)
        dist_km = dist_m / 1000
        pace = (elapsed / 60) / dist_km if dist_km > 0 else 0

        activities.append({
            "id": str(a["id"]),
            "date": a["start_date_local"][:10],
            "datetime": a["start_date_local"],
            "name": a.get("name", ""),
            "distance_m": round(dist_m, 1),
            "distance_km": round(dist_km, 2),
            "elapsed_seconds": elapsed,
            "moving_seconds": moving,
            "avg_hr": round(a.get("average_heartrate", 0)),
            "max_hr": round(a.get("max_heartrate", 0)),
            "elevation_gain": round(a.get("total_elevation_gain", 0)),
            "pace_min_per_km": round(pace, 2),
        })

    # Sort newest first
    activities.sort(key=lambda x: x["datetime"], reverse=True)
    return activities


def compute_weekly_summaries(activities):
    """Aggregate activities into weekly summaries."""
    week_data = {}
    for a in activities:
        dt = datetime.strptime(a["date"], "%Y-%m-%d")
        week_start = dt - timedelta(days=dt.weekday())
        wk = week_start.strftime("%Y-%m-%d")
        if wk not in week_data:
            week_data[wk] = {"week_start": wk, "runs": 0, "distance_km": 0, "time_min": 0, "avg_hr_sum": 0, "elevation": 0}
        week_data[wk]["runs"] += 1
        week_data[wk]["distance_km"] += a["distance_km"]
        week_data[wk]["time_min"] += a["elapsed_seconds"] / 60
        week_data[wk]["avg_hr_sum"] += a["avg_hr"]
        week_data[wk]["elevation"] += a["elevation_gain"]

    weeks = []
    for wk in sorted(week_data.keys()):
        d = week_data[wk]
        d["distance_km"] = round(d["distance_km"], 1)
        d["time_min"] = round(d["time_min"])
        d["avg_hr"] = round(d["avg_hr_sum"] / d["runs"]) if d["runs"] > 0 else 0
        del d["avg_hr_sum"]
        weeks.append(d)
    return weeks


def main():
    print("Fetching Strava access token...")
    token = get_access_token()

    print("Fetching activities...")
    raw = fetch_activities(token)
    print(f"Fetched {len(raw)} total activities")

    activities = process_activities(raw)
    print(f"Processed {len(activities)} runs")

    weeks = compute_weekly_summaries(activities)
    print(f"Computed {len(weeks)} weekly summaries")

    output = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "athlete": {"name": "Felix", "weight_kg": 81},
        "activities": activities,
        "weekly_summaries": weeks,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/activities.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("Written data/activities.json")


if __name__ == "__main__":
    main()
