"""Instagram influencer shortlist — profiles, recent posts and bio contacts in one pass.

Use case: you have a list of candidate creators for a campaign and need to know,
before anyone sends a DM, which of them are worth paying. This script:

  1. pulls every candidate's profile (followers, category, verification, bio links),
  2. pulls their most recent posts and computes a real engagement rate
     (average likes + comments per post divided by followers) and posting cadence,
  3. pulls bio contacts (public emails, phones, links) for creators that pass the bar,
  4. writes a ranked shortlist to output.json and output.csv.

No Instagram login is needed for any of the three modes used here.

Run:
    pip install -r requirements.txt
    cp .env.example .env
    python main.py

Actor: https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dotenv import load_dotenv

ACTOR_ID = "pro100chok/instagram-scraper-all-in-one"

# Candidate creators for a home-fitness campaign. Usernames, @handles and
# profile URLs are all accepted by the actor.
CANDIDATES = [
    "kayla_itsines",
    "blogilates",
    "thebodycoach",
    "chloe_t",
    "sydneycummings",
    "https://www.instagram.com/natashaoakley/",
]
POSTS_PER_CREATOR = 12         # recent posts used for the engagement maths
MIN_ENGAGEMENT_RATE = 0.5      # percent; creators below this are dropped
OUT_DIR = Path(__file__).parent


def run_actor(client: ApifyClient, run_input: dict, label: str) -> list[dict]:
    print(f"  -> {label}")
    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=1800)
    except ApifyApiError as exc:
        sys.exit(f"{label} failed: {exc}")
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"     {len(items)} records")
    return items


def posts_per_week(timestamps: list[int]) -> float | None:
    """Posting cadence from unix timestamps of the newest posts."""
    ts = sorted(t for t in timestamps if t)
    if len(ts) < 2:
        return None
    span_days = max((ts[-1] - ts[0]) / 86400, 1)
    return round(len(ts) / span_days * 7, 2)


def main() -> int:
    load_dotenv()
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        sys.exit("APIFY_API_TOKEN missing — copy .env.example to .env first.")
    client = ApifyClient(token)

    print("Step 1/3 — profiles")
    profiles = run_actor(client, {
        "scrapeType": "profile",
        "directUrls": CANDIDATES,
        "resultsLimit": 1,
    }, "profile mode")
    by_user = {p["username"].lower(): p for p in profiles if p.get("username")}

    print("Step 2/3 — recent posts")
    posts = run_actor(client, {
        "scrapeType": "posts",
        "directUrls": list(by_user),
        "resultsLimit": POSTS_PER_CREATOR,
    }, f"posts mode, {POSTS_PER_CREATOR} per creator")
    posts_by_user: dict[str, list[dict]] = defaultdict(list)
    for p in posts:
        if p.get("ownerUsername"):
            posts_by_user[p["ownerUsername"].lower()].append(p)

    rows = []
    for username, prof in by_user.items():
        followers = prof.get("followersCount") or 0
        recent = posts_by_user.get(username, [])
        # Accounts that hide like counts return no likesCount — skip those posts.
        interactions = [(p.get("likesCount") or 0) + (p.get("commentsCount") or 0)
                        for p in recent if p.get("likesCount") is not None]
        avg_inter = mean(interactions) if interactions else 0
        er = round(avg_inter / followers * 100, 3) if followers else 0
        rows.append({
            "username": prof.get("username"),
            "fullName": prof.get("fullName"),
            "category": prof.get("category"),
            "isVerified": prof.get("isVerified"),
            "followersCount": followers,
            "postsCount": prof.get("postsCount"),
            "postsSampled": len(recent),
            "avgLikesPlusComments": round(avg_inter),
            "engagementRatePct": er,
            "postsPerWeek": posts_per_week([p.get("timestamp") for p in recent]),
            "videoShare": round(sum(1 for p in recent if p.get("isVideo")) / len(recent), 2)
            if recent else None,
            "topHashtags": ", ".join(sorted(
                {h for p in recent for h in (p.get("hashtags") or [])})[:8]),
            "externalUrl": prof.get("externalUrl"),
            "url": prof.get("url"),
        })

    shortlist = [r for r in rows if r["engagementRatePct"] >= MIN_ENGAGEMENT_RATE]
    shortlist.sort(key=lambda r: -r["engagementRatePct"])

    print(f"Step 3/3 — bio contacts for {len(shortlist)} shortlisted creators")
    if shortlist:
        contacts = run_actor(client, {
            "scrapeType": "contacts",
            "directUrls": [r["username"] for r in shortlist],
            "resultsLimit": 1,
        }, "contacts mode")
        contact_by_user = {c["username"].lower(): c for c in contacts if c.get("username")}
        for r in shortlist:
            c = contact_by_user.get(r["username"].lower(), {})
            r["email"] = c.get("email")
            r["phone"] = c.get("phone")
            r["businessCategory"] = c.get("businessCategory")
            r["links"] = " | ".join(c.get("links") or [])

    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (OUT_DIR / "output.json").write_text(json.dumps(
        {"generatedAt": stamp, "shortlist": shortlist, "all": rows},
        indent=2, ensure_ascii=False), encoding="utf-8")
    if shortlist:
        with (OUT_DIR / "output.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(shortlist[0].keys()))
            writer.writeheader()
            writer.writerows(shortlist)

    print(f"\n{'creator':<22}{'followers':>12}{'ER %':>8}{'posts/wk':>10}  email")
    for r in shortlist:
        print(f"{r['username']:<22}{r['followersCount']:>12,}{r['engagementRatePct']:>8}"
              f"{str(r['postsPerWeek'] or '-'):>10}  {r.get('email') or '-'}")
    dropped = len(rows) - len(shortlist)
    print(f"\nShortlisted {len(shortlist)} of {len(rows)} creators "
          f"({dropped} below {MIN_ENGAGEMENT_RATE}% ER). Saved output.json / output.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
