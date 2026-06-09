# -*- coding: utf-8 -*-
"""
Long-running logging loop for GitHub Actions.

Problem with plain cron: GitHub throttles/delays scheduled workflows, so a
"*/10" schedule actually fires every 1-2 hours, irregularly. Instead, ONE
workflow run stays alive here and snapshots every 5 minutes for ~5.5 hours
(under the 6h job cap), committing each snapshot. A frequent cron + a
concurrency guard then starts the next run right after this one ends, so the
logging is dense and regular regardless of cron timing.

Env knobs (used for local testing; the workflow uses the defaults):
  RUN_MINUTES   total run time before clean exit   (default 340)
  INTERVAL      seconds between snapshots           (default 300 = 5 min)
  MAX_SNAPSHOTS stop after N snapshots, 0 = no cap  (default 0)
  DO_GIT        "1" commit+push each snapshot, "0" skip (default 1)
"""
import os
import time
import datetime
import subprocess
import log_status as L

RUN_MINUTES = int(os.environ.get("RUN_MINUTES", "340"))
INTERVAL = int(os.environ.get("INTERVAL", "300"))
MAX_SNAPSHOTS = int(os.environ.get("MAX_SNAPSHOTS", "0"))
DO_GIT = os.environ.get("DO_GIT", "1") == "1"


def git(*args):
    subprocess.run(["git", *args], check=False)


def commit_push(stamp):
    git("add", "data")
    # commit only if something actually changed
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0:
        git("commit", "-m", f"log: {stamp} [skip ci]")
        git("pull", "--rebase", "--autostash")
        git("push")


def main():
    feeds = L.feed_urls()
    L.save_station_information(feeds["station_information"])
    deadline = time.time() + RUN_MINUTES * 60
    count = 0
    while time.time() < deadline:
        start = time.time()
        try:
            L.log_status(feeds["station_status"])
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
            if DO_GIT:
                commit_push(stamp)
        except Exception as e:
            print("snapshot error:", e)
        count += 1
        if MAX_SNAPSHOTS and count >= MAX_SNAPSHOTS:
            print(f"reached MAX_SNAPSHOTS={MAX_SNAPSHOTS}, exiting")
            break
        # keep a steady cadence regardless of how long the snapshot took
        time.sleep(max(1, INTERVAL - (time.time() - start)))
    print(f"loop finished after {count} snapshots")


if __name__ == "__main__":
    main()
