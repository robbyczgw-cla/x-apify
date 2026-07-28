#!/usr/bin/env python3
"""
Fetch X/Twitter data via Apify API with local caching.

Usage:
    python3 fetch_tweets.py --search "query"
    python3 fetch_tweets.py --user "username"
    python3 fetch_tweets.py --url "https://x.com/user/status/123"
    python3 fetch_tweets.py --search "query" --xquik
    python3 fetch_tweets.py --followers "username"
    python3 fetch_tweets.py --cache-stats
    python3 fetch_tweets.py --clear-cache

Actor execution requires APIFY_API_TOKEN and requests. Planning does not.
"""

import os
import sys
import time

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
except ImportError:
    requests = None

from config import (
    APIFY_API_BASE,
    DEFAULT_MAX_RESULTS,
    XQUIK_FOLLOWER_ACTOR_ID,
    XQUIK_TWEET_ACTOR_ID,
    get_api_token,
    get_actor_id,
    is_allowed_output_path,
    sanitize_query,
)
from cache import (
    load_from_cache,
    save_to_cache,
    clear_cache,
    print_cache_stats,
)
from arguments import build_parser
from formatting import (
    format_audience_results,
    format_output_json,
    format_output_summary,
    format_results,
)
from xquik_routes import (
    actor_cache_identifier,
    build_audience_input,
    build_search_input,
    build_tweet_input,
    build_user_input,
    build_xquik_cli_plan,
    get_audience_selection,
    normalize_tweet_url,
    normalize_username_target,
)


def run_apify_actor(input_data, api_token, actor_id=None):
    """Run an Apify Actor and return its default dataset rows."""
    if requests is None:
        print("Error: 'requests' library not installed.", file=sys.stderr)
        print("Install with: pip install requests", file=sys.stderr)
        sys.exit(1)
    actor_id = actor_id or get_actor_id()
    run_id = _start_actor_run(input_data, api_token, actor_id)
    dataset_id = _wait_for_actor(run_id, api_token)
    return _fetch_dataset(dataset_id, api_token)


def _auth_headers(api_token, include_content_type=False):
    headers = {"Authorization": f"Bearer {api_token}"}
    if include_content_type:
        headers["Content-Type"] = "application/json"
    return headers


def _start_actor_run(input_data, api_token, actor_id):
    run_url = f"{APIFY_API_BASE}/acts/{actor_id}/runs"

    try:
        response = requests.post(
            run_url,
            headers=_auth_headers(api_token, include_content_type=True),
            json=input_data,
            timeout=30,
        )

        if response.status_code == 401:
            print("Error: Invalid API token.", file=sys.stderr)
            sys.exit(1)

        if response.status_code == 402:
            print("Error: Apify quota exceeded. Check your billing:", file=sys.stderr)
            print("https://console.apify.com/billing", file=sys.stderr)
            sys.exit(1)

        response.raise_for_status()
        return response.json()["data"]["id"]
    except requests.exceptions.RequestException as error:
        print(f"Error starting Apify actor: {error}", file=sys.stderr)
        sys.exit(1)


def _wait_for_actor(run_id, api_token):
    status_url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
    start_time = time.time()

    while time.time() - start_time < 180:
        try:
            response = requests.get(
                status_url,
                headers=_auth_headers(api_token),
                timeout=10,
            )
            response.raise_for_status()
            status_data = response.json()["data"]
            status = status_data["status"]

            if status == "SUCCEEDED":
                return status_data["defaultDatasetId"]
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                print(f"Error: Apify actor {status.lower()}.", file=sys.stderr)
                sys.exit(1)

            time.sleep(3)
        except requests.exceptions.RequestException as error:
            print(f"Error checking status: {error}", file=sys.stderr)
            sys.exit(1)

    print("Error: Timeout waiting for Apify actor.", file=sys.stderr)
    sys.exit(1)


def _fetch_dataset(dataset_id, api_token):
    dataset_url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items"

    try:
        response = requests.get(
            dataset_url,
            headers=_auth_headers(api_token),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching results: {error}", file=sys.stderr)
        sys.exit(1)


def search_tweets(query, max_results, api_token, use_cache, actor_id=None):
    """Search for tweets by query."""
    actor_id = actor_id or get_actor_id()
    query = sanitize_query(query)
    if not query:
        print("Error: Empty search query.", file=sys.stderr)
        sys.exit(1)
    cache_identifier = actor_cache_identifier(
        actor_id,
        f"{query}:{max_results}",
    )
    
    # Check cache
    if use_cache:
        cached = load_from_cache('search', cache_identifier)
        if cached:
            print(f"[cached] Search results for: {query}", file=sys.stderr)
            return cached, True
    
    print(f"Searching tweets for: {query}", file=sys.stderr)
    
    input_data = build_search_input(query, max_results, actor_id)
    results = run_apify_actor(input_data, api_token, actor_id)
    
    # Format results
    formatted = format_results('search', query, results)
    
    # Save to cache
    if use_cache:
        save_to_cache('search', cache_identifier, formatted)
    
    return formatted, False


def get_user_tweets(username, max_results, api_token, use_cache, actor_id=None):
    """Get tweets from a specific user."""
    actor_id = actor_id or get_actor_id()
    try:
        username = normalize_username_target(username)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    cache_identifier = actor_cache_identifier(
        actor_id,
        f"{username}:{max_results}",
    )
    
    # Check cache
    if use_cache:
        cached = load_from_cache('user', cache_identifier)
        if cached:
            print(f"[cached] Tweets from: @{username}", file=sys.stderr)
            return cached, True
    
    print(f"Fetching tweets from: @{username}", file=sys.stderr)
    
    input_data = build_user_input(username, max_results, actor_id)
    results = run_apify_actor(input_data, api_token, actor_id)
    
    # Format results
    formatted = format_results('user', username, results)
    
    # Save to cache
    if use_cache:
        save_to_cache('user', cache_identifier, formatted)
    
    return formatted, False


def get_tweet_by_url(
    url,
    api_token,
    use_cache,
    max_results=50,
    actor_id=None,
):
    """Get a specific tweet and its replies by URL."""
    actor_id = actor_id or get_actor_id()
    try:
        url, tweet_id = normalize_tweet_url(url)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    cache_identifier = actor_cache_identifier(
        actor_id,
        f"{tweet_id}:{max_results}",
    )
    
    # Check cache
    if use_cache:
        cached = load_from_cache('url', cache_identifier)
        if cached:
            print(f"[cached] Tweet: {tweet_id}", file=sys.stderr)
            return cached, True
    
    print(f"Fetching tweet: {tweet_id}", file=sys.stderr)
    
    input_data = build_tweet_input(url, max_results, actor_id)
    results = run_apify_actor(input_data, api_token, actor_id)
    
    # Format results
    formatted = format_results('url', url, results)
    
    # Save to cache
    if use_cache:
        save_to_cache('url', cache_identifier, formatted)
    
    return formatted, False


def get_audience(
    username,
    relation,
    max_results,
    api_token,
    use_cache,
):
    """Get an X audience relation through Xquik X Follower Scraper."""
    try:
        username = normalize_username_target(username)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    mode = f"audience-{relation}"
    cache_identifier = actor_cache_identifier(
        XQUIK_FOLLOWER_ACTOR_ID,
        f"{username}:{max_results}",
    )

    if use_cache:
        cached = load_from_cache(mode, cache_identifier)
        if cached:
            print(
                f"[cached] {relation.replace('_', ' ')} for: @{username}",
                file=sys.stderr,
            )
            return cached, True

    print(
        f"Fetching {relation.replace('_', ' ')} for: @{username}",
        file=sys.stderr,
    )
    input_data = build_audience_input(username, relation, max_results)
    results = run_apify_actor(
        input_data,
        api_token,
        XQUIK_FOLLOWER_ACTOR_ID,
    )
    formatted = format_audience_results(relation, username, results)

    if use_cache:
        save_to_cache(mode, cache_identifier, formatted)

    return formatted, False


def _handle_cache_command(args):
    if args.clear_cache:
        clear_cache()
        return True
    if args.cache_stats:
        print_cache_stats()
        return True
    return False


def _validate_route(parser, args):
    relation, audience_target = get_audience_selection(args)
    has_post_mode = args.search or args.user or args.url

    if not has_post_mode and not audience_target:
        parser.print_help()
        print(
            "\nError: Specify a post or audience mode.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.max_results < 1:
        parser.error("--max-results must be at least 1")

    is_xquik_route = args.xquik or bool(audience_target)
    if args.execute and not is_xquik_route:
        parser.error("--execute is only valid with --xquik or an audience mode")
    return relation, audience_target, is_xquik_route


def _print_plan_or_continue(parser, args, is_xquik_route):
    if is_xquik_route and not args.execute:
        try:
            plan = build_xquik_cli_plan(args)
        except ValueError as error:
            parser.error(str(error))
        print(format_output_json(plan))
        return False
    return True


def _execute_route(args, relation, audience_target):
    api_token = get_api_token()
    use_cache = not args.no_cache
    actor_id = XQUIK_TWEET_ACTOR_ID if args.xquik else get_actor_id()

    if args.search:
        return search_tweets(
            args.search,
            args.max_results,
            api_token,
            use_cache,
            actor_id,
        )
    if args.user:
        return get_user_tweets(
            args.user,
            args.max_results,
            api_token,
            use_cache,
            actor_id,
        )
    if args.url:
        return get_tweet_by_url(
            args.url,
            api_token,
            use_cache,
            args.max_results,
            actor_id,
        )
    return get_audience(
        audience_target,
        relation,
        args.max_results,
        api_token,
        use_cache,
    )


def _write_output(args, data):
    if args.format == "json":
        output = format_output_json(data)
    else:
        output = format_output_summary(data)

    if args.output:
        safe_dir = os.path.dirname(os.path.abspath(__file__))
        is_allowed, out_path = is_allowed_output_path(args.output, safe_dir)
        if not is_allowed:
            print(
                f"Error: output path must be under {safe_dir} or /tmp",
                file=sys.stderr,
            )
            sys.exit(1)
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as output_file:
            output_file.write(output)
        print(f"Results saved to: {out_path}", file=sys.stderr)
    else:
        print(output)


def main():
    parser = build_parser(DEFAULT_MAX_RESULTS)
    args = parser.parse_args()
    if _handle_cache_command(args):
        return

    relation, audience_target, is_xquik_route = _validate_route(parser, args)
    if not _print_plan_or_continue(parser, args, is_xquik_route):
        return

    data, from_cache = _execute_route(args, relation, audience_target)
    _write_output(args, data)

    if not from_cache:
        print("\n[Apify credits used - check https://console.apify.com/billing]", file=sys.stderr)


if __name__ == "__main__":
    main()
