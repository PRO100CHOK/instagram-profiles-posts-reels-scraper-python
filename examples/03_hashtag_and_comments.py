"""Hashtag research, then the conversation under the most-liked post.

Step 1 pulls posts under a hashtag; step 2 pulls comments for the most-liked one.
Both modes return their first page without a login. Put your Instagram cookie in
INSTAGRAM_SESSION_COOKIE (see .env.example) to page deeper — it is passed to the
actor's `sessionCookie` field and nowhere else.

Actor: https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

HASHTAG = "#vanlife"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])
actor = client.actor("pro100chok/instagram-scraper-all-in-one")
cookie = os.environ.get("INSTAGRAM_SESSION_COOKIE") or None


def with_cookie(run_input: dict) -> dict:
    return {**run_input, "sessionCookie": cookie} if cookie else run_input


run = actor.call(run_input=with_cookie({
    "scrapeType": "hashtag",
    "directUrls": [HASHTAG],
    "resultsLimit": 60,
}))
posts = list(client.dataset(run["defaultDatasetId"]).iterate_items())
print(f"{len(posts)} posts under {HASHTAG} (login: {'yes' if cookie else 'no'})")
if not posts:
    raise SystemExit("Nothing returned — the biggest hashtags need a login cookie.")

top = max(posts, key=lambda p: p.get("likesCount") or 0)
print(f"Most-liked post: {top.get('url')} by @{top.get('ownerUsername')}")

run = actor.call(run_input=with_cookie({
    "scrapeType": "comments",
    "directUrls": [top["url"]],
    "resultsLimit": 100,
}))
for c in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"  [{c.get('likesCount') or 0:>4} likes, {c.get('repliesCount') or 0} replies] "
          f"@{c.get('ownerUsername')}: {(c.get('text') or '')[:100]}")
