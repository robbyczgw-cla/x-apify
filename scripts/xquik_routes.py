"""Bounded Xquik Actor inputs and plan helpers."""

from urllib.parse import urlparse

from config import (
    XQUIK_FOLLOWER_ACTOR_ID,
    XQUIK_TWEET_ACTOR_ID,
    extract_tweet_id,
    extract_username_from_url,
    sanitize_query,
    sanitize_username,
)

AUDIENCE_RELATIONS = (
    "followers",
    "following",
    "verified_followers",
)
X_HOSTS = ("x.com", "twitter.com")


def is_xquik_tweet_actor(actor_id):
    """Return whether an Actor identifier selects Xquik X Tweet Scraper."""
    return actor_id in (XQUIK_TWEET_ACTOR_ID, "wAusCMrm284Voaw86")


def require_positive_max_results(max_results):
    """Reject unbounded or invalid result caps."""
    if max_results < 1:
        raise ValueError("max_results must be at least 1")


def build_search_input(query, max_results, actor_id):
    """Build a bounded search payload for the selected Tweet Actor."""
    require_positive_max_results(max_results)
    input_data = {
        "searchTerms": [query],
        "maxItems": max_results,
    }
    if is_xquik_tweet_actor(actor_id):
        input_data.update({
            "mode": "search",
            "queryType": "Latest + Top",
            "includeSearchTerms": True,
            "outputVariant": "rich",
            "fieldStyle": "camelCase",
            "outputPreset": "nested",
            "maxItemsPerTarget": max_results,
        })
    return input_data


def build_user_input(username, max_results, actor_id):
    """Build a bounded profile-timeline payload."""
    require_positive_max_results(max_results)
    if is_xquik_tweet_actor(actor_id):
        return {
            "mode": "profileTweets",
            "twitterHandles": [username],
            "outputVariant": "rich",
            "fieldStyle": "camelCase",
            "outputPreset": "nested",
            "maxItems": max_results,
            "maxItemsPerTarget": max_results,
        }
    return {
        "startUrls": [{"url": f"https://x.com/{username}"}],
        "maxItems": max_results,
    }


def build_tweet_input(url, max_results, actor_id):
    """Build a bounded post payload."""
    require_positive_max_results(max_results)
    if is_xquik_tweet_actor(actor_id):
        return {
            "mode": "tweet",
            "postUrls": [url],
            "outputVariant": "rich",
            "fieldStyle": "camelCase",
            "outputPreset": "nested",
            "maxItems": max_results,
            "maxItemsPerTarget": max_results,
        }
    return {
        "startUrls": [{"url": url}],
        "maxItems": max_results,
    }


def build_audience_input(username, relation, max_results):
    """Build a bounded Xquik audience payload."""
    require_positive_max_results(max_results)
    if relation not in AUDIENCE_RELATIONS:
        raise ValueError(
            "relation must be one of: {}".format(", ".join(AUDIENCE_RELATIONS))
        )
    return {
        "twitterHandles": [username],
        "relation": relation,
        "outputMode": "compact",
        "includeTargetMetadata": True,
        "dedupeMode": "merge",
        "maxItems": max_results,
        "maxItemsPerTarget": max_results,
    }


def build_plan(actor_id, input_data):
    """Build a no-cost Actor plan for review."""
    return {
        "execute": False,
        "actor_id": actor_id,
        "input": input_data,
        "message": "Review live Actor pricing and this input. Add --execute only after approval.",
    }


def normalize_username_target(target):
    """Normalize an @handle or X/Twitter profile URL."""
    target_url = _normalize_x_url(target)
    username = (
        extract_username_from_url(target_url)
        if target_url
        else sanitize_username(target)
    )
    if not username:
        raise ValueError("Invalid username.")
    return username


def normalize_tweet_url(url):
    """Validate a post target and return a full URL."""
    target_url = _normalize_x_url(url)
    tweet_id = extract_tweet_id(target_url or url)
    if not tweet_id:
        raise ValueError(f"Could not extract tweet ID from: {url}")
    if target_url:
        return target_url, tweet_id
    return f"https://x.com/i/status/{tweet_id}", tweet_id


def _normalize_x_url(value):
    value = (value or "").strip()
    if not value:
        return None

    candidate = value
    if value.startswith(("x.com/", "twitter.com/")):
        candidate = f"https://{value}"
    elif "://" not in value:
        return None

    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower()
    if not any(
        hostname == root or hostname.endswith(f".{root}")
        for root in X_HOSTS
    ):
        raise ValueError("URL must use x.com or twitter.com.")
    return candidate


def actor_cache_identifier(actor_id, identifier):
    """Keep cached results isolated by Actor."""
    return f"{actor_id}:{identifier}"


def partition_result_rows(raw_results):
    """Separate data rows from Xquik diagnostics and run reports."""
    rows = []
    diagnostics = []
    run_reports = []

    for item in raw_results:
        if not isinstance(item, dict):
            continue
        result_type = item.get("resultType") or item.get("result_type")
        if result_type == "diagnostic":
            diagnostics.append(item)
        elif result_type in ("run-report", "run_report"):
            run_reports.append(item)
        else:
            rows.append(item)

    return rows, diagnostics, run_reports


def get_audience_selection(args):
    """Return the selected audience relation and target."""
    for relation, argument_name in (
        ("followers", "followers"),
        ("following", "following"),
        ("verified_followers", "verified_followers"),
    ):
        target = getattr(args, argument_name, None)
        if target:
            return relation, target
    return None, None


def build_xquik_cli_plan(args, tweet_actor_id=XQUIK_TWEET_ACTOR_ID):
    """Build the exact Xquik request selected on the command line."""
    relation, target = get_audience_selection(args)
    if relation:
        username = normalize_username_target(target)
        input_data = build_audience_input(
            username,
            relation,
            args.max_results,
        )
        return build_plan(XQUIK_FOLLOWER_ACTOR_ID, input_data)

    if args.search:
        query = sanitize_query(args.search)
        if not query:
            raise ValueError("Empty search query.")
        input_data = build_search_input(
            query,
            args.max_results,
            tweet_actor_id,
        )
    elif args.user:
        username = normalize_username_target(args.user)
        input_data = build_user_input(
            username,
            args.max_results,
            tweet_actor_id,
        )
    else:
        url, _ = normalize_tweet_url(args.url)
        input_data = build_tweet_input(
            url,
            args.max_results,
            tweet_actor_id,
        )

    return build_plan(tweet_actor_id, input_data)
