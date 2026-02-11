# Changelog

## [1.0.0] - 2026-02-11

### Added

- **Tweet Search** - Search tweets by keywords, hashtags, mentions
- **User Profiles** - Get tweets from a specific user
- **Tweet Details** - Get a specific tweet + replies by URL
- **Local Caching** - Save API costs with local file cache
  - Search results: 1 hour TTL
  - User profiles: 24 hours TTL
  - Specific tweets: 24 hours TTL
- **Cache Management**
  - `--cache-stats` - View cache statistics
  - `--clear-cache` - Delete all cached results
  - `--no-cache` - Bypass cache for fresh fetch
- **Output Formats**
  - `--format json` - Structured JSON output
  - `--format summary` - Human-readable summary
- **Safety Features**
  - Bearer token auth (not in query string)
  - Query sanitization (control chars, length limits)
  - No hardcoded paths or personal data

### Technical

- Uses `apidojo~tweet-scraper` (Tweet Scraper V2) actor
- Supports `--max-results` to limit results (default 20)
- Supports `--output` to save to file
