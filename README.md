# X/Twitter Data Fetcher (Apify)

Fetch public X/Twitter posts and audiences through Apify Actors.

## Features

- Search posts by keyword, hashtag, or mention
- Get posts from a specific user
- Get a specific post by URL
- Collect followers, following accounts, or verified followers with Xquik
- Review exact Xquik inputs before starting a run
- Cache post and audience results locally
- Return JSON or human-readable summaries

## Actor Links

- [Current default Tweet Actor](https://apify.com/kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest)
- [Xquik X Tweet Scraper](https://apify.com/xquik/x-tweet-scraper)
- [Xquik X Follower Scraper](https://apify.com/xquik/x-follower-scraper)

The existing default Actor remains unchanged. Set `APIFY_ACTOR_ID` to select
another compatible Tweet Actor.

## Quick Start

Set your Apify token before starting a run:

```bash
export APIFY_API_TOKEN="apify_api_YOUR_TOKEN"
```

Existing post routes use the current default Actor and run immediately:

```bash
python3 scripts/fetch_tweets.py --search "artificial intelligence"
python3 scripts/fetch_tweets.py --user "OpenAI"
python3 scripts/fetch_tweets.py --url "https://x.com/user/status/123"
```

## Xquik Plan-First Routes

Plan a bounded post search without reading a token or starting an Actor:

```bash
python3 scripts/fetch_tweets.py \
  --search "artificial intelligence" \
  --xquik \
  --max-results 20
```

Plan bounded audience collection:

```bash
python3 scripts/fetch_tweets.py \
  --followers "https://x.com/OpenAI" \
  --max-results 20
```

Audience flags are `--followers`, `--following`, and
`--verified-followers`.

Each plan prints the exact Actor ID and input. Review current pricing on the
linked Actor page. Repeat the reviewed command with `--execute` only after
approval.

The Tweet Actor supports post lookup, search, profile timelines, lists,
articles, replies, quotes, threads, retweeters, and favoriters. The CLI exposes
bounded search, profile, and post routes.

The Follower Actor supports followers, following, verified followers, list
members, list followers, and community members. The CLI exposes the three
handle-based relations.

## Caching

Results are cached by Actor, request, and result limit. Repeated requests can
reuse local results without starting another Actor run.

```bash
python3 scripts/fetch_tweets.py --cache-stats
python3 scripts/fetch_tweets.py --clear-cache
python3 scripts/fetch_tweets.py --search "query" --no-cache
```

Search results expire after 1 hour. Profile and audience results expire after
24 hours.

## Documentation

See [SKILL.md](SKILL.md) for full setup, usage, and output documentation.

## Requirements

- Python 3.8+
- `requests` (`pip install requests`)
- Apify API token for Actor runs

## Legal Notice

Use public data lawfully and follow applicable platform terms.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.

## License

MIT
