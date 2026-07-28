import json
import subprocess
import sys
import unittest
from pathlib import Path

REPOSITORY_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPOSITORY_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_tweets


class ActorInputTests(unittest.TestCase):
    def test_existing_actor_search_input_is_preserved(self):
        payload = fetch_tweets.build_search_input(
            "product launch",
            20,
            "existing~actor",
        )

        self.assertEqual(
            payload,
            {
                "searchTerms": ["product launch"],
                "maxItems": 20,
            },
        )

    def test_xquik_post_inputs_are_explicit_and_bounded(self):
        payload = fetch_tweets.build_search_input(
            "product launch",
            25,
            fetch_tweets.XQUIK_TWEET_ACTOR_ID,
        )

        self.assertEqual(payload["mode"], "search")
        self.assertEqual(payload["outputVariant"], "rich")
        self.assertEqual(payload["maxItems"], 25)
        self.assertEqual(payload["maxItemsPerTarget"], 25)

    def test_xquik_audience_input_preserves_target_metadata(self):
        payload = fetch_tweets.build_audience_input(
            "example",
            "verified_followers",
            30,
        )

        self.assertEqual(payload["twitterHandles"], ["example"])
        self.assertEqual(payload["relation"], "verified_followers")
        self.assertTrue(payload["includeTargetMetadata"])
        self.assertEqual(payload["dedupeMode"], "merge")
        self.assertEqual(payload["maxItems"], 30)
        self.assertEqual(payload["maxItemsPerTarget"], 30)

    def test_nonpositive_result_caps_are_rejected(self):
        with self.assertRaises(ValueError):
            fetch_tweets.build_search_input(
                "query",
                0,
                fetch_tweets.XQUIK_TWEET_ACTOR_ID,
            )

    def test_non_x_post_urls_are_rejected(self):
        with self.assertRaises(ValueError):
            fetch_tweets.normalize_tweet_url(
                "https://example.com/user/status/1234567890"
            )


class ResultHandlingTests(unittest.TestCase):
    def test_api_token_stays_in_authorization_header(self):
        headers = fetch_tweets._auth_headers(
            "secret-token",
            include_content_type=True,
        )

        self.assertEqual(
            headers,
            {
                "Authorization": "Bearer secret-token",
                "Content-Type": "application/json",
            },
        )

    def test_diagnostics_and_run_reports_are_not_tweets(self):
        rows = [
            {"id": "1", "text": "hello"},
            {"resultType": "diagnostic", "status": "zero-output"},
            {"resultType": "run-report", "estimatedChargeUsd": 0},
        ]

        formatted = fetch_tweets.format_results("search", "hello", rows)

        self.assertEqual(formatted["count"], 1)
        self.assertEqual(len(formatted["diagnostics"]), 1)
        self.assertEqual(len(formatted["run_reports"]), 1)

    def test_cache_identifiers_are_isolated_by_actor(self):
        default_key = fetch_tweets.actor_cache_identifier(
            "existing~actor",
            "query:20",
        )
        xquik_key = fetch_tweets.actor_cache_identifier(
            fetch_tweets.XQUIK_TWEET_ACTOR_ID,
            "query:20",
        )

        self.assertNotEqual(default_key, xquik_key)

    def test_output_path_check_uses_directory_boundaries(self):
        allowed, _ = fetch_tweets.is_allowed_output_path(
            "/tmp/results.json",
            str(SCRIPTS_DIR),
        )
        sibling_allowed, _ = fetch_tweets.is_allowed_output_path(
            "/tmp-not-allowed/results.json",
            str(SCRIPTS_DIR),
        )

        self.assertTrue(allowed)
        self.assertFalse(sibling_allowed)


class PlanCliTests(unittest.TestCase):
    def run_plan(self, *arguments, environment=None):
        process_environment = {"PYTHONIOENCODING": "utf-8"}
        if environment:
            process_environment.update(environment)
        completed = subprocess.run(
            [
                sys.executable,
                "-S",
                str(SCRIPTS_DIR / "fetch_tweets.py"),
                *arguments,
            ],
            cwd=str(REPOSITORY_DIR),
            env=process_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_post_plan_needs_no_token(self):
        plan = self.run_plan(
            "--search",
            "product launch",
            "--xquik",
            "--max-results",
            "12",
        )

        self.assertFalse(plan["execute"])
        self.assertEqual(
            plan["actor_id"],
            fetch_tweets.XQUIK_TWEET_ACTOR_ID,
        )
        self.assertEqual(plan["input"]["maxItems"], 12)

    def test_audience_plan_needs_no_token(self):
        plan = self.run_plan(
            "--followers",
            "https://x.com/example",
            "--max-results",
            "14",
        )

        self.assertFalse(plan["execute"])
        self.assertEqual(
            plan["actor_id"],
            fetch_tweets.XQUIK_FOLLOWER_ACTOR_ID,
        )
        self.assertEqual(plan["input"]["twitterHandles"], ["example"])

    def test_environment_selected_xquik_actor_is_plan_first(self):
        for actor_id in (
            fetch_tweets.XQUIK_TWEET_ACTOR_ID,
            "wAusCMrm284Voaw86",
        ):
            with self.subTest(actor_id=actor_id):
                plan = self.run_plan(
                    "--search",
                    "product launch",
                    environment={"APIFY_ACTOR_ID": actor_id},
                )

                self.assertFalse(plan["execute"])
                self.assertEqual(plan["actor_id"], actor_id)
                self.assertEqual(plan["input"]["mode"], "search")


if __name__ == "__main__":
    unittest.main()
