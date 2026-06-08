# -*- coding: utf-8 -*-
"""
Snapshot BIXI's live GBFS station-status feed into a daily CSV.

Why this exists: completed BIXI trip history only shows rides that HAPPENED.
It cannot show a station that sat empty (no bikes) or full (no docks) — i.e.
unmet demand. The live GBFS feed shows the current state but has no memory,
so we record it ourselves every few minutes to build that history.

Stdlib only (urllib/json/csv) so GitHub Actions needs no pip install.
"""
import urllib.request
import json
import csv
import os
import datetime

GBFS_INDEX = "https://gbfs.velobixi.com/gbfs/2-2/gbfs.json"
DATA_DIR = "data"
UA = {"User-Agent": "bixi-tourist-project-logger/1.0 (educational use)"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def feed_urls():
    """Resolve the sub-feed URLs from the GBFS index (language-agnostic)."""
    idx = get_json(GBFS_INDEX)
    langs = idx["data"]
    block = langs.get("en") or next(iter(langs.values()))
    return {f["name"]: f["url"] for f in block["feeds"]}


def save_station_information(url):
    """Static station info (name, lat, lon, capacity) — written once."""
    path = os.path.join(DATA_DIR, "station_information.csv")
    if os.path.exists(path):
        return
    stations = get_json(url)["data"]["stations"]
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["station_id", "name", "lat", "lon", "capacity"])
        for s in stations:
            w.writerow([s.get("station_id"), s.get("name"), s.get("lat"),
                        s.get("lon"), s.get("capacity")])
    print(f"wrote station_information.csv ({len(stations)} stations)")


def log_status(url):
    """Append one row per station for this moment into today's CSV (UTC)."""
    data = get_json(url)["data"]["stations"]
    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    day = now.strftime("%Y-%m-%d")
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"status_{day}.csv")
    is_new = not os.path.exists(path)
    cols = ["snapshot_utc", "station_id", "num_bikes_available",
            "num_ebikes_available", "num_docks_available",
            "num_bikes_disabled", "num_docks_disabled",
            "is_installed", "is_renting", "is_returning", "last_reported"]
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(cols)
        for s in data:
            w.writerow([stamp, s.get("station_id"),
                        s.get("num_bikes_available"),
                        s.get("num_ebikes_available"),
                        s.get("num_docks_available"),
                        s.get("num_bikes_disabled"),
                        s.get("num_docks_disabled"),
                        s.get("is_installed"),
                        s.get("is_renting"),
                        s.get("is_returning"),
                        s.get("last_reported")])
    print(f"logged {len(data)} stations at {stamp} -> {path}")


if __name__ == "__main__":
    feeds = feed_urls()
    save_station_information(feeds["station_information"])
    log_status(feeds["station_status"])
