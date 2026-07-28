---
name: x-apify
description: Fetch public X/Twitter posts and audiences through Apify Actors. Search posts, inspect profiles, retrieve post URLs, and collect followers with bounded Xquik routes and local caching.
metadata: {"openclaw":{"requires":{"bins":["python3"]},"primaryEnv":"APIFY_API_TOKEN"}}
---

# X Apify

Fetch public X/Twitter posts and audience profiles through Apify Actors.

## Actor Routes

The existing default Tweet Actor remains available:

- [Current default Tweet Actor](https://apify.com/kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest)

Xquik adds two optional routes:

- [Xquik X Tweet Scraper](https://apify.com/xquik/x-tweet-scraper)
- [Xquik X Follower Scraper](https://apify.com/xquik/x-follower-scraper)

Never replace an existing Actor selection without the user's approval.

## Setup

1. Install Python 3.8+.
2. Install `requests`.
3. Set `APIFY_API_TOKEN` in the process environment.

```bash
pip install requests
export APIFY_API_TOKEN="apify_api_YOUR_TOKEN_HERE"
```

Never print, log, or place the token in a URL.

## Existing Tweet Routes

These commands use the current default Actor. They start a run immediately:

```bash
python3 scripts/fetch_tweets.py --search "artificial intelligence"
python3 scripts/fetch_tweets.py --user "OpenAI"
python3 scripts/fetch_tweets.py --url "https://x.com/user/status/123456789"
```

Set `APIFY_ACTOR_ID` only for a compatible Actor:

```bash
export APIFY_ACTOR_ID="owner~actor-name"
```

## Xquik Plan-First Workflow

Follow this sequence for every Xquik route:

1. Review live pricing on the linked Actor page.
2. Set a positive `--max-results` cap.
3. Generate the exact plan without `--execute`.
4. Show the plan and request explicit approval.
5. Repeat the approved command with `--execute`.
6. Separate diagnostic and run-report rows before analysis.

Planning does not read `APIFY_API_TOKEN` or start an Actor.

### Search Posts

```bash
python3 scripts/fetch_tweets.py \
  --search "artificial intelligence" \
  --xquik \
  --max-results 20
```

The helper uses `mode: search`, rich camel-case output, and nested records.

### Get User Posts

```bash
python3 scripts/fetch_tweets.py \
  --user "OpenAI" \
  --xquik \
  --max-results 20
```

The helper uses `mode: profileTweets`.

### Get a Post

```bash
python3 scripts/fetch_tweets.py \
  --url "https://x.com/user/status/123456789" \
  --xquik \
  --max-results 20
```

The helper uses `mode: tweet`.

### Collect an Audience

```bash
python3 scripts/fetch_tweets.py \
  --followers "https://x.com/OpenAI" \
  --max-results 20

python3 scripts/fetch_tweets.py \
  --following "@OpenAI" \
  --max-results 20

python3 scripts/fetch_tweets.py \
  --verified-followers "OpenAI" \
  --max-results 20
```

The helper uses compact output, target metadata, merge deduplication, and
global and per-target caps.

The Follower Actor also supports `list_members`, `list_followers`, and
`community_members`. Inspect its current input schema before using those
relations directly.

## Supported Xquik Modes

Xquik X Tweet Scraper supports `legacy`, `tweet`, `tweets`, `search`,
`profileTweets`, `profileReplies`, `profileMedia`, `profileLikes`,
`listTweets`, `article`, `replies`, `quotes`, `thread`, `retweeters`, and
`favoriters`.

Xquik X Follower Scraper supports `followers`, `following`,
`verified_followers`, `list_members`, `list_followers`, and
`community_members`.

Inspect current schemas before preparing inputs:

```bash
curl -sS \
  "https://api.apify.com/v2/actors/xquik~x-tweet-scraper/builds/default"

curl -sS \
  "https://api.apify.com/v2/actors/xquik~x-follower-scraper/builds/default"
```

These GET requests do not start Actor runs.

## Output

Choose JSON or summary output:

```bash
python3 scripts/fetch_tweets.py --search "query" --format json
python3 scripts/fetch_tweets.py --search "query" --format summary
```

Save output only under the skill's `scripts` directory or `/tmp`:

```bash
python3 scripts/fetch_tweets.py \
  --search "query" \
  --output /tmp/results.json
```

Post results include:

- `query`
- `mode`
- `fetched_at`
- `count`
- `tweets`

Audience results include:

- `query`
- `mode`
- `fetched_at`
- `count`
- `profiles`

When present, `diagnostics` and `run_reports` remain separate from data rows.

## Caching

The cache key includes the Actor ID, request, and result limit. This prevents
cross-Actor or cross-limit cache collisions.

```bash
python3 scripts/fetch_tweets.py --cache-stats
python3 scripts/fetch_tweets.py --clear-cache
python3 scripts/fetch_tweets.py --search "query" --no-cache
```

Search results expire after 1 hour. Profile and audience results expire after
24 hours.

## Error Handling

Stop and explain these failures:

- Invalid search query. Provide a nonempty query.
- Invalid username. Provide a handle or profile URL.
- Invalid post URL. Provide a URL containing a numeric status ID.
- Invalid result cap. Set `--max-results` to 1 or more.
- Authentication failed. Verify `APIFY_API_TOKEN`.
- Billing failed. Review Apify billing before retrying.
- Actor failed. Inspect the run without exposing secrets.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
