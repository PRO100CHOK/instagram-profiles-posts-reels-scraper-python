# Instagram Profiles, Posts & Reels Scraper — Python Example

> Scrape Instagram profiles, posts, reels, comments, hashtags and bio emails from Python, with no Instagram login for the core modes and no Graph API app review.

[![Apify Actor](https://img.shields.io/badge/Apify-Actor-blue)](https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

A small, working Python project built on the [Instagram Scraper API actor on Apify](https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python). One actor covers **15 scrape modes**. Pick a mode, pass usernames, post links or hashtags, and you get back flat JSON records ready for pandas, a CSV file or a Google Sheet.

## What this does

Meta's official Instagram Graph API only shows you data for accounts you manage, or business accounts you look up one at a time after an app review. If you want to research creators, benchmark competitors or collect posts under a hashtag, that API is no help. This actor works as an **unofficial Instagram API**: you call it over HTTP and get back the public data instagram.com shows in a browser.

Your Python code only chooses a `scrapeType`, lists its targets in `directUrls` and reads the dataset. Each record has a `type` field (`profile`, `post`, `contact`, `comment`, `user`, `story`, `searchResult`), and each run also stores the `inputUrl` it came from, so you can join results back to your input list.

### Which modes need a login

| Works without login | First page without login, deeper with a cookie | Needs a login cookie |
|---|---|---|
| `profile`, `contacts`, `posts`, `reels`, `post` | `comments`, `hashtag` | `likes`, `followers`, `following`, `tagged`, `stories`, `highlights`, `location`, `search` |

For the cookie modes, pass your own session in `sessionCookie`. It accepts a cookie-export JSON, a bare `sessionid` value or a `name=value; ...` string. The examples here read it from the `INSTAGRAM_SESSION_COOKIE` environment variable so it never ends up in your code.

## Use cases

- **Influencer vetting.** Work out a real engagement rate from recent posts before you pay for a sponsored post. `main.py` does this end to end.
- **Creator and brand lead generation.** Contacts mode returns public business emails, phone numbers, bio links and business address for each account.
- **Competitor benchmarking.** Track follower count, post count and highlights for a set of rival brands week by week.
- **Content research.** Collect an account's posts or reels with captions, hashtags, mentions, likes, comments, media URLs and carousel slides.
- **Hashtag and UGC discovery.** See who posts under a campaign hashtag and which posts get the most attention.
- **Audience and sentiment research.** Pull comments under a post with text, author, like count and reply count.

## Requirements

- Python **3.10+**
- A free [Apify account](https://console.apify.com/sign-up). Each month includes $5 of usage credit.
- No Instagram account for the no-login modes. An Instagram cookie only for the modes marked as needing one.

## Quick start

```bash
git clone https://github.com/pro100chok/instagram-profiles-posts-reels-scraper-python.git
cd instagram-profiles-posts-reels-scraper-python
pip install -r requirements.txt
cp .env.example .env
# paste your APIFY_API_TOKEN into .env
python main.py
```

`main.py` builds an **influencer shortlist** for a home-fitness campaign in three runs:

1. **`profile` mode** fetches followers, category and verification for each candidate.
2. **`posts` mode** fetches each candidate's 12 newest posts. The script averages likes plus comments per post and divides by followers to get an engagement rate, then works out posting cadence from post timestamps.
3. **`contacts` mode** fetches public emails, phones and links, but only for creators above your engagement threshold, so you don't pay for leads you would throw away.

You get a ranked `output.csv` and a full `output.json`. To reuse it for another niche, change `CANDIDATES` and `MIN_ENGAGEMENT_RATE`.

## How it works

```python
import os
from apify_client import ApifyClient

client = ApifyClient(os.environ["APIFY_API_TOKEN"])
run = client.actor("pro100chok/instagram-scraper-all-in-one").call(run_input={
    "scrapeType": "reels",
    "directUrls": ["https://www.instagram.com/natgeo/", "@nasa"],
    "resultsLimit": 30,
})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["shortCode"], item.get("likesCount"), item.get("videoUrl"))
```

`directUrls` is forgiving about what you put in it. Profile modes accept `nasa`, `@nasa` or the full profile URL. Post modes accept `/p/` and `/reel/` links. Hashtag mode accepts `#nature`, `nature` or the explore-tag URL. If you give a post URL to a profile mode, the actor resolves it to the post's author. If you give a profile to a post mode, it falls back to that profile's latest posts. `resultsLimit` caps the records **per input** (from 1 to 100,000), and pagination stops early when the source runs out.

## Example output

A post record, shortened:

```json
{
  "type": "post",
  "shortCode": "DZz4bjIjhdm",
  "url": "https://www.instagram.com/p/DZz4bjIjhdm/",
  "mediaType": "carousel",
  "caption": "The official FIFA World Cup ball went to space",
  "hashtags": ["space", "fifa"],
  "mentions": ["fifa"],
  "likesCount": 917834,
  "commentsCount": 3287,
  "timestamp": 1782490000,
  "ownerUsername": "nasa",
  "displayUrl": "https://instagram.f...jpg",
  "images": ["https://...1.jpg", "https://...2.jpg"],
  "childPosts": [
    {"mediaType": "image", "displayUrl": "https://...1.jpg", "dimensionsWidth": 1080, "dimensionsHeight": 1350},
    {"mediaType": "video", "videoUrl": "https://...2.mp4", "dimensionsWidth": 1080, "dimensionsHeight": 1920}
  ],
  "taggedUsers": ["fifa"],
  "accessibilityCaption": "Photo by NASA ...",
  "firstComment": "This is incredible",
  "inputUrl": "https://www.instagram.com/nasa/"
}
```

A **profile** record includes `followersCount`, `followsCount`, `postsCount`, `highlightReelCount`, `biography`, `externalUrl`, `bioLinks`, `category`, `isVerified`, `isBusinessAccount`, `relatedProfiles` and a `latestPosts` preview. A **contact** record includes `email`/`emails`, `phone`/`phones`, `website`, `links`, `bioMentions`, `businessCategory`, `addressStreet`/`addressCity`/`addressZip` and `followersCount`. Fields Instagram leaves empty are dropped from the record, not sent as `null`. `timestamp` is a Unix time in seconds.

Without a login, Instagram no longer gives out video view and play counts, the pinned and paid-partnership flags, or a reel's music details. If you add a cookie, those fields come back.

## Input parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `scrapeType` | string | `posts` | `profile`, `contacts`, `posts`, `reels`, `post`, `comments`, `likes`, `followers`, `following`, `tagged`, `stories`, `highlights`, `hashtag`, `location`, `search` |
| `directUrls` | string[] | — | Usernames, profile / post / reel / hashtag / location URLs. Leave empty in `search` mode. |
| `search` | string | — | Free-text query, used only in `search` mode. |
| `searchType` | string | `all` | `all`, `user`, `hashtag`, `place` (search mode only). |
| `resultsLimit` | integer | `100` | Max records per input, 1–100,000. |
| `sessionCookie` | string | — | Instagram cookie for login modes. It is stored encrypted on Apify. |
| `maxRetries` | integer | `6` | Retries per failed request (1–20). |

You don't need to configure proxies. Anti-blocking is built into the actor.

## More examples

| File | What it shows |
|---|---|
| `examples/01_basic_usage.py` | The 20 newest posts of one account, with date, likes and comments. |
| `examples/02_bio_contacts_leads.py` | Emails, phones and bio links for a list of brands. |
| `examples/03_hashtag_and_comments.py` | Hashtag posts, then the comments under the most-liked one, with an optional cookie. |
| `examples/04_export_to_csv.py` | Engagement by media type in pandas, plus one CSV row per carousel slide. |
| `examples/05_export_to_google_sheets.py` | A weekly competitor follower tracker in a Google Sheet. |

## Ready-made tasks

These are preconfigured runs on Apify. Open one and click Start:

- [Get Instagram profile data and follower counts](https://apify.com/pro100chok/instagram-scrape-profile-details?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python)
- [Extract emails and contacts from Instagram bios](https://apify.com/pro100chok/instagram-extract-contacts-from-bio?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python)
- [Export all posts from an Instagram account](https://apify.com/pro100chok/instagram-export-account-posts?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python)
- [Export Instagram reels from an account](https://apify.com/pro100chok/instagram-export-account-reels?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python)
- [Research Instagram posts behind any hashtag](https://apify.com/pro100chok/instagram-hashtag-content-research?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python)

## Pricing

The actor charges pay-per-result, with a separate price for each record type. There is no monthly rental. Prices per 1,000 records:

| Record | Free plan | Paid plans (from) |
|---|---|---|
| Post / reel | $3.00 | $0.90 |
| Profile | $4.00 | $1.00 |
| Contact (bio lead) | $6.00 | $2.00 |
| Comment | $1.00 | $0.40 |
| Follower / following / liker | $1.00 | $0.40 |
| Story / highlight | $2.00 | $1.00 |
| Search result | $2.00 | $0.70 |

There is also a $0.00005 fee each time the actor starts. On the Free plan, the $5 monthly credit pays for about 1,600 posts or 1,250 profiles.

## FAQ

**Is this the official Instagram API?**
No. It reads the same public pages instagram.com shows to visitors. It does not need a Meta developer app, and it can look up accounts you don't manage.

**Can I scrape Instagram without logging in?**
Yes, in the profile, contacts, posts, reels and post-detail modes. Comments and hashtag return their first page without a login. The other modes need a cookie from your own account.

**How do I get emails from Instagram profiles?**
Use `scrapeType: "contacts"`. It collects the public business email and phone, any emails or phone numbers written in the bio, bio links and the business address. See `examples/02_bio_contacts_leads.py`.

**Can I download carousel images and reel videos?**
Each post has `displayUrl`, `videoUrl`, `images` and `videos`. Each slide in `childPosts` has its own image or video URL with its pixel size. Media URLs from Instagram expire after a while, so download the files soon after the run.

**Why don't I see view counts on reels?**
Instagram stopped sending play counts to logged-out visitors. If you pass `sessionCookie`, `videoPlayCount`, `videoViewCount` and `musicInfo` come back.

**Can I scrape private accounts?**
Only accounts that the account behind your cookie already follows. Public accounts work in every mode.

**How do I keep costs predictable?**
Keep `resultsLimit` low while testing, and set a maximum cost per run in the Apify console. You pay only for records that are actually returned, so an input that returns nothing costs nothing beyond the start fee.

## Related actors

- [TikTok Profile API Scraper + Contacts](https://apify.com/pro100chok/tiktok-profile-pro?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python) — TikTok creator stats and bio contacts for cross-platform influencer research.
- [Threads Scraper — Posts, Profiles & Replies](https://apify.com/pro100chok/threads-scraper-usage?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python) — Meta's Threads, which many Instagram creators also post to.
- [Facebook Ads Library Scraper](https://apify.com/pro100chok/meta-ads-library-scraper?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python) — the paid side: Meta and Instagram ads a brand is running.
- [YouTube Scraper API](https://apify.com/pro100chok/youtube-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python) — videos, Shorts, comments and channel emails.
- [Pinterest Full Scraper](https://apify.com/pro100chok/pinterest-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python) — pins, boards and creator profiles for visual-trend research.

## License

MIT. See [LICENSE](LICENSE). Use the data in line with Instagram's terms and the privacy laws that apply to you.

---

Built by [pro100chok](https://apify.com/pro100chok/instagram-scraper-all-in-one?utm_source=github_pro100&utm_medium=readme&utm_campaign=instagram-profiles-posts-reels-scraper-python) on Apify.
