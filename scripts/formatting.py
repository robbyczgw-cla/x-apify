"""Output normalization and rendering."""

import json
from datetime import datetime, timezone

from xquik_routes import partition_result_rows


def format_results(mode, identifier, raw_results):
    """Format raw Apify results into standardized output."""
    result_rows, diagnostics, run_reports = partition_result_rows(raw_results)
    tweets = []

    for item in result_rows:
        author_obj = item.get("author") or item.get("user") or {}
        screen_name = (
            author_obj.get("userName")
            or author_obj.get("screen_name", "")
        )
        author_name = author_obj.get("name", screen_name)
        tweet_id = item.get("id") or item.get("id_str", "")
        tweet = {
            "id": str(tweet_id),
            "text": item.get("text", item.get("full_text", "")),
            "author": screen_name,
            "author_name": author_name,
            "created_at": item.get(
                "createdAt",
                item.get("created_at", ""),
            ),
            "likes": item.get(
                "likeCount",
                item.get("favorite_count", 0),
            ),
            "retweets": item.get(
                "retweetCount",
                item.get("retweet_count", 0),
            ),
            "replies": item.get(
                "replyCount",
                item.get("conversation_count", 0),
            ),
            "url": item.get("url", item.get("twitterUrl", "")),
        }

        if not tweet["url"] and tweet["author"] and tweet["id"]:
            tweet["url"] = (
                f"https://x.com/{tweet['author']}/status/{tweet['id']}"
            )

        tweets.append(tweet)

    formatted = {
        "query": identifier,
        "mode": mode,
        "fetched_at": _utc_now(),
        "count": len(tweets),
        "tweets": tweets,
    }
    _add_control_rows(formatted, diagnostics, run_reports)
    return formatted


def format_audience_results(relation, username, raw_results):
    """Keep profile rows intact and isolate non-profile records."""
    profiles, diagnostics, run_reports = partition_result_rows(raw_results)
    formatted = {
        "query": username,
        "mode": f"audience-{relation}",
        "fetched_at": _utc_now(),
        "count": len(profiles),
        "profiles": profiles,
    }
    _add_control_rows(formatted, diagnostics, run_reports)
    return formatted


def _utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _add_control_rows(formatted, diagnostics, run_reports):
    if diagnostics:
        formatted["diagnostics"] = diagnostics
    if run_reports:
        formatted["run_reports"] = run_reports


def format_output_json(data):
    """Format data as a JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_output_summary(data):
    """Format data as a human-readable summary."""
    if data["mode"].startswith("audience-"):
        return _format_audience_summary(data)
    return _format_tweet_summary(data)


def _format_audience_summary(data):
    relation = data["mode"][len("audience-"):].replace("_", " ")
    lines = [
        f"=== X/Twitter {relation.title()} ===",
        f"Query: @{data['query']}",
        f"Fetched: {data['fetched_at']}",
        f"Results: {data['count']} profiles",
        "",
    ]

    for profile in data["profiles"]:
        username = profile.get("username", "")
        name = profile.get("name", username)
        lines.extend([
            "---",
            f"@{username} ({name})",
            "Followers: {} | Following: {}".format(
                profile.get("followers", 0),
                profile.get("following", 0),
            ),
        ])
        if profile.get("description"):
            lines.append(profile["description"])
        if profile.get("sourceUrl"):
            lines.append(profile["sourceUrl"])
        lines.append("")

    return "\n".join(lines)


def _format_tweet_summary(data):
    mode_labels = {
        "search": "Search Results",
        "user": "User Tweets",
        "url": "Tweet Details",
    }
    lines = [
        f"=== X/Twitter {mode_labels.get(data['mode'], 'Results')} ===",
        f"Query: {data['query']}",
        f"Fetched: {data['fetched_at']}",
        f"Results: {data['count']} tweets",
        "",
    ]

    for tweet in data["tweets"]:
        lines.extend([
            "---",
            f"@{tweet['author']} ({tweet['author_name']})",
            f"{tweet['created_at']}",
            tweet["text"],
            (
                f"[Likes: {tweet['likes']} | RTs: {tweet['retweets']} | "
                f"Replies: {tweet['replies']}]"
            ),
        ])
        if tweet["url"]:
            lines.append(tweet["url"])
        lines.append("")

    return "\n".join(lines)
