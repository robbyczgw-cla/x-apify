"""Command-line arguments for the X Apify skill."""

import argparse


def build_parser(default_max_results):
    parser = argparse.ArgumentParser(
        description="Fetch X/Twitter data via Apify API with local caching"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--search", "-s",
        metavar="QUERY",
        help="Search tweets by keywords, hashtags, mentions",
    )
    mode_group.add_argument(
        "--user", "-u",
        metavar="USERNAME",
        help="Get tweets from a specific user",
    )
    mode_group.add_argument(
        "--url",
        metavar="URL",
        help="Get a specific tweet and replies by URL",
    )
    mode_group.add_argument(
        "--followers",
        metavar="USERNAME",
        help="Get followers with Xquik X Follower Scraper",
    )
    mode_group.add_argument(
        "--following",
        metavar="USERNAME",
        help="Get following accounts with Xquik X Follower Scraper",
    )
    mode_group.add_argument(
        "--verified-followers",
        metavar="USERNAME",
        help="Get verified followers with Xquik X Follower Scraper",
    )

    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=default_max_results,
        help=f"Maximum results to fetch (default: {default_max_results})",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "summary"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--xquik",
        action="store_true",
        help="Use Xquik X Tweet Scraper for post routes",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Start a planned Xquik Actor run after approval",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache (always fetch fresh)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached results and exit",
    )
    parser.add_argument(
        "--cache-stats",
        action="store_true",
        help="Show cache statistics and exit",
    )
    return parser
