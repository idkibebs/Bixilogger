# BIXI GBFS Logger

Records BIXI's live station-availability feed every ~10 minutes so we can measure
**when and where stations run empty (no bikes) or full (no docks)** — information
that the BIXI trip-history files *cannot* give us (they only show rides that
happened, never unmet demand).

It runs on **GitHub Actions** (GitHub's free servers), so it keeps logging
24/7 even when your own computer is off.

## What it produces (in the `data/` folder)
- `station_information.csv` — one row per station: id, name, lat, lon, capacity (written once).
- `status_YYYY-MM-DD.csv` — one file per day; one row per station per snapshot:
  `snapshot_utc, station_id, num_bikes_available, num_ebikes_available,
  num_docks_available, num_bikes_disabled, num_docks_disabled, is_installed,
  is_renting, is_returning, last_reported`.

A station with `num_bikes_available = 0` was **empty**; `num_docks_available = 0`
was **full**. Counting those moments per station = our stockout/availability data.

## One-time setup
1. Create a free account at **github.com** (if you don't have one).
2. Create a **new repository** — name it e.g. `bixi-logger`, set it **Public**
   (public repos get unlimited free Actions minutes; the data is open anyway).
3. Upload these files into the repo, keeping the folder structure:
   - `log_status.py`
   - `.github/workflows/logger.yml`
   - `README.md`
   (You can drag-and-drop on github.com via "Add file → Upload files", but the
   `.github/workflows/` folder must be created exactly — easier to push with git,
   see below.)
4. In the repo: **Settings → Actions → General → Workflow permissions** →
   select **"Read and write permissions"** → Save. (This lets the logger save data back.)
5. Go to the **Actions** tab → enable workflows if prompted → open
   **"BIXI GBFS logger"** → **Run workflow** to test it once.
6. After it succeeds, check the `data/` folder — you'll see the first CSVs.
   From now on it runs automatically every ~10 minutes.

## Pushing with git (recommended over drag-drop)
From inside this folder:
```
git init
git add .
git commit -m "initial: BIXI GBFS logger"
git branch -M main
git remote add origin https://github.com/<your-username>/bixi-logger.git
git push -u origin main
```

## Using the data later
Clone or download the repo, then in Python:
```python
import pandas as pd, glob
status = pd.concat([pd.read_csv(f) for f in glob.glob("data/status_*.csv")])
stations = pd.read_csv("data/station_information.csv")
df = status.merge(stations, on="station_id")
# empty episodes:
empty = df[df.num_bikes_available == 0]
```

## Notes
- Scheduled runs are in **UTC** and can be delayed a few minutes (sometimes skipped)
  under GitHub load — fine for our purpose.
- Data grows ~10–12 MB/day. To shrink it, change the cron in `logger.yml` to
  `*/15` or `*/20` (every 15/20 min), or filter to tourist-zone stations later.
- Scheduled workflows pause after 60 days of no repo activity — the logger's own
  commits count as activity, so it stays alive through the project.
