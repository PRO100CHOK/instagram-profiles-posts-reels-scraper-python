"""Weekly competitor follower tracker in a Google Sheet.

Setup:
  1. Google Cloud console -> create a service account -> download its JSON key.
  2. Save it as service_account.json next to this file (it is gitignored).
  3. Share the target spreadsheet with the service account's email address.
  4. Put the accounts you benchmark in BRANDS.

Each run appends one dated row per brand, so the sheet turns into a follower and
post-count time series. Schedule it weekly on Apify or with cron.

Actor: https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python
"""
import os
from datetime import datetime, timezone

import gspread
from apify_client import ApifyClient
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

SPREADSHEET = "Instagram competitor tracker"
WORKSHEET = "weekly"
BRANDS = ["nike", "adidas", "puma", "newbalance", "underarmour", "asics"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/instagram-scraper-all-in-one").call(run_input={
    "scrapeType": "profile",
    "directUrls": BRANDS,
    "resultsLimit": 1,
})

header = ["date", "username", "full_name", "followers", "following", "posts",
          "highlights", "verified", "category", "latest_post_likes", "external_url"]
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
rows = []
for p in client.dataset(run["defaultDatasetId"]).iterate_items():
    latest = (p.get("latestPosts") or [{}])[0]
    rows.append([
        today, p.get("username"), p.get("fullName"), p.get("followersCount"),
        p.get("followsCount"), p.get("postsCount"), p.get("highlightReelCount"),
        p.get("isVerified"), p.get("category"), latest.get("likesCount"),
        p.get("externalUrl"),
    ])

creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
sheet = gspread.authorize(creds).open(SPREADSHEET)
try:
    ws = sheet.worksheet(WORKSHEET)
except gspread.WorksheetNotFound:
    ws = sheet.add_worksheet(WORKSHEET, rows=5000, cols=len(header))
    ws.append_row(header)

ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Appended {len(rows)} brand snapshots for {today} to {SPREADSHEET}/{WORKSHEET}")
