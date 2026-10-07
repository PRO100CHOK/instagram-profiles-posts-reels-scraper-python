"""Turn a list of Instagram accounts into an outreach list — emails, phones, links.

Contacts mode reads each profile's public business email / phone, any emails or
phone numbers written in the bio, bio links and business address. No login.
Accounts that publish no contact details simply come back without an `email`.

Actor: https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python
"""
import os

from apify_client import ApifyClient
from dotenv import load_dotenv

ACCOUNTS = ["gymshark", "myprotein", "bodybuildingcom", "optimumnutrition", "musclepharm"]

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

run = client.actor("pro100chok/instagram-scraper-all-in-one").call(run_input={
    "scrapeType": "contacts",
    "directUrls": ACCOUNTS,
    "resultsLimit": 1,
})

with_email = 0
for c in client.dataset(run["defaultDatasetId"]).iterate_items():
    with_email += bool(c.get("email"))
    print(f"@{c.get('username'):<24} {c.get('followersCount') or 0:>11,} followers  "
          f"{(c.get('businessCategory') or '-')[:22]}")
    print(f"    email : {', '.join(c.get('emails') or []) or '-'}")
    print(f"    phone : {', '.join(c.get('phones') or []) or '-'}")
    print(f"    links : {' | '.join(c.get('links') or []) or '-'}")
    if c.get("addressCity"):
        print(f"    city  : {c['addressCity']}")

print(f"\n{with_email}/{len(ACCOUNTS)} accounts publish an email address")
