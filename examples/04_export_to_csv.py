"""Post and carousel performance report with pandas — exported to CSV.

Pulls an account's posts, splits carousels into one row per slide (from
`childPosts`), and writes two files:
  output.csv         one row per post, with engagement and media type
  output_slides.csv  one row per carousel slide, with its image/video URL and size

Actor: https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python
"""
import os

import pandas as pd
from apify_client import ApifyClient
from dotenv import load_dotenv

ACCOUNT = "nike"

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/instagram-scraper-all-in-one").call(run_input={
    "scrapeType": "posts",
    "directUrls": [ACCOUNT],
    "resultsLimit": 60,
})
items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
if not items:
    raise SystemExit("No posts returned.")

df = pd.DataFrame(items)
for col in ("likesCount", "commentsCount"):
    if col not in df.columns:
        df[col] = 0
df["posted"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
df["engagement"] = df["likesCount"].fillna(0) + df["commentsCount"].fillna(0)
df["hashtags"] = df["hashtags"].apply(lambda h: " ".join(h) if isinstance(h, list) else "")
cols = ["posted", "shortCode", "mediaType", "productType", "engagement", "likesCount",
        "commentsCount", "hashtags", "displayUrl", "videoUrl", "url"]
df = df[[c for c in cols if c in df.columns]].sort_values("engagement", ascending=False)
df.to_csv("output.csv", index=False)

print("Engagement by media type:")
print(df.groupby("mediaType")["engagement"].agg(["count", "mean", "max"]).round(0))

slides = [
    {"post": p.get("shortCode"), "slide": i + 1,
     **{k: s.get(k) for k in ("mediaType", "displayUrl", "videoUrl", "dimensionsWidth",
                              "dimensionsHeight", "accessibilityCaption")}}
    for p in items for i, s in enumerate(p.get("childPosts") or [])
]
pd.DataFrame(slides).to_csv("output_slides.csv", index=False)
print(f"\nSaved {len(df)} posts to output.csv and {len(slides)} slides to output_slides.csv")
