"""Latest 20 posts from one public Instagram account — no login.

`directUrls` takes a username, an @handle or a full profile URL.

Actor: https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python
"""
import os
from datetime import datetime, timezone

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/instagram-scraper-all-in-one").call(run_input={
    "scrapeType": "posts",
    "directUrls": ["natgeo"],
    "resultsLimit": 20,
})

for p in client.dataset(run["defaultDatasetId"]).iterate_items():
    ts = p.get("timestamp")
    when = datetime.fromtimestamp(ts, timezone.utc).date() if ts else "-"
    caption = (p.get("caption") or "").strip().splitlines()
    print(f"{when}  {p.get('mediaType') or '?':<8} {p.get('likesCount') or 0:>9,} likes  "
          f"{p.get('commentsCount') or 0:>6,} comments  {p.get('url')}")
    print(f"    {caption[0][:110] if caption else ''}")
