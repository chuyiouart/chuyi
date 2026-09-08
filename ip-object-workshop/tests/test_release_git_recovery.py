"""Offline regression: real Git repositories, no production/network access."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import release_daily as rd

DAY = "2026-09-08"
ARTICLE = f"ip-object-workshop/updates/{DAY}-example.html"
ALLOWLIST = ["ip-object-workshop/course-calendar.json", "ip-object-workshop/course-updates.js", "ip-object-workshop/index.html", ARTICLE]


class GitRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.remote = self.root / "chuyiouart/chuyi.git"
        self.remote.parent.mkdir()
        self.call(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.repo = self.root / "nas"
        self.writer = self.root / "other-writer"
        self.call(self.root, "clone", self.remote.as_posix(), str(self.repo))
        self.configure(self.repo)
        for path in ALLOWLIST:
            self.write(self.repo, path, "base\n")
        self.write(self.repo, "ip-object-workshop/scripts/workshop_publish.py", "# publisher\n")
        self.write(self.repo, "daily-art.txt", "old\n")
        self.commit(self.repo, "initial fixture")
        self.call(self.repo, "push", "origin", "main")
        self.call(self.root, "clone", self.remote.as_posix(), str(self.writer))
        self.configure(self.writer)

    def tearDown(self):
        self.temp.cleanup()

    def call(self, repo, *args, check=True):
        result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True)
        if check and result.returncode:
            self.fail(f"git {args}: {result.stdout}\n{result.stderr}")
        return result

    def configure(self, repo):
        for key, value in (("user.name", "Release test"), ("user.email", "test@example.invalid"), ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
            self.call(repo, "config", key, value)

    def write(self, repo, path, content):
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def commit(self, repo, subject):
        self.call(repo, "add", "--all")
        self.call(repo, "commit", "-m", subject)
        return self.call(repo, "rev-parse", "HEAD").stdout.strip()

    def local_release(self, text="today\n"):
        self.write(self.repo, ARTICLE, text)
        return self.commit(self.repo, f"content: publish workshop update {DAY}")

    def upstream_change(self, path="daily-art.txt", text="new\n"):
        self.call(self.writer, "pull", "--ff-only", "origin", "main")
        self.write(self.writer, path, text)
        commit = self.commit(self.writer, "content: another lane")
        self.call(self.writer, "push", "origin", "main")
        return commit

    def remote_head(self):
        return self.call(self.repo, "ls-remote", "origin", "refs/heads/main").stdout.split()[0]

    def test_local_commit_and_disjoint_remote_both_preserved(self):
        local = self.local_release()
        upstream = self.upstream_change()
        sync = rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)
        self.assertEqual(sync["action"], "verified_merge")
        self.assertTrue(rd.is_ancestor(self.repo, local, "HEAD"))
        self.assertTrue(rd.is_ancestor(self.repo, upstream, "HEAD"))
        self.assertEqual((self.repo / ARTICLE).read_text(), "today\n")
        self.assertEqual((self.repo / "daily-art.txt").read_text(), "new\n")
        result = rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None)
        self.assertTrue(result["pushed"])
        self.assertEqual(self.remote_head(), self.call(self.repo, "rev-parse", "HEAD").stdout.strip())

    def test_conflict_detected_without_mutating_checkout(self):
        head = self.local_release("local\n")
        upstream = self.upstream_change(ARTICLE, "remote\n")
        with self.assertRaisesRegex(RuntimeError, "merge conflict"):
            rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)
        self.assertEqual(self.call(self.repo, "rev-parse", "HEAD").stdout.strip(), head)
        self.assertEqual((self.repo / ARTICLE).read_text(), "local\n")
        self.assertFalse((self.repo / ".git/MERGE_HEAD").exists())
        self.assertEqual(self.call(self.repo, "status", "--porcelain").stdout, "")
        self.assertEqual(self.remote_head(), upstream)

    def test_unknown_local_commit_never_pushed_or_merged(self):
        self.write(self.repo, "private-draft.txt", "user work\n")
        head = self.commit(self.repo, "draft: unfinished user work")
        upstream = self.upstream_change()
        with self.assertRaisesRegex(RuntimeError, "unrecognized unpublished commit"):
            rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None)
        self.assertEqual(self.call(self.repo, "rev-parse", "HEAD").stdout.strip(), head)
        self.assertEqual(self.remote_head(), upstream)

    def test_release_subject_cannot_smuggle_unrelated_files(self):
        self.write(self.repo, "private-draft.txt", "user work\n")
        head = self.commit(self.repo, f"content: publish workshop update {DAY}")
        with self.assertRaisesRegex(RuntimeError, "exceeds current release allowlist"):
            rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)
        self.assertEqual(self.call(self.repo, "rev-parse", "HEAD").stdout.strip(), head)

    def test_unrelated_staged_or_unstaged_changes_preserved(self):
        for staged in (False, True):
            with self.subTest(staged=staged):
                self.write(self.repo, "daily-art.txt", "unfinished\n")
                if staged:
                    self.call(self.repo, "add", "daily-art.txt")
                before = self.call(self.repo, "status", "--porcelain").stdout
                with self.assertRaisesRegex(RuntimeError, "dirty"):
                    rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)
                self.assertEqual(self.call(self.repo, "status", "--porcelain").stdout, before)
                self.assertEqual((self.repo / "daily-art.txt").read_text(), "unfinished\n")

    def test_upstream_race_reconciles_and_retries_normal_push(self):
        local = self.local_release()
        real_git = rd.git
        pushes = []

        def racing_git(repo, *args, **kwargs):
            if args and args[0] == "push":
                pushes.append(args)
                if len(pushes) == 1:
                    self.upstream_change()
            return real_git(repo, *args, **kwargs)

        with patch.object(rd, "git", side_effect=racing_git):
            result = rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None)
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(len(pushes), 2)
        self.assertTrue(all("--force" not in command and "+HEAD" not in str(command) for command in pushes))
        self.assertTrue(rd.is_ancestor(self.repo, local, "HEAD"))
        self.assertEqual((self.repo / "daily-art.txt").read_text(), "new\n")

    def test_race_retry_limit_preserves_commits(self):
        local = self.local_release()
        real_git = rd.git
        calls = []

        def always_racing(repo, *args, **kwargs):
            if args and args[0] == "push":
                calls.append(args)
                self.upstream_change(text=f"race {len(calls)}\n")
            return real_git(repo, *args, **kwargs)

        with patch.object(rd, "git", side_effect=always_racing):
            with self.assertRaisesRegex(RuntimeError, "failed after 2 attempt"):
                rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None, attempts=2)
        self.assertEqual(len(calls), 2)
        self.assertTrue(rd.is_ancestor(self.repo, local, "HEAD"))
        self.assertEqual(self.call(self.repo, "status", "--porcelain").stdout, "")

    def test_uncertain_successful_push_is_idempotent_on_readback(self):
        self.local_release()
        real_git = rd.git
        calls = []

        def uncertain_git(repo, *args, **kwargs):
            value = real_git(repo, *args, **kwargs)
            if args and args[0] == "push":
                calls.append(args)
                return subprocess.CompletedProcess(args, 1, "", "Connection reset by peer")
            return value

        with patch.object(rd, "git", side_effect=uncertain_git), patch.object(rd.time, "sleep"):
            result = rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None)
        self.assertTrue(result["already_remote"])
        self.assertEqual(len(calls), 1)

    def test_fast_forward_and_already_remote_need_no_push(self):
        upstream = self.upstream_change()
        self.assertEqual(rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)["action"], "fast_forward")
        result = rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None)
        self.assertTrue(result["already_remote"])
        self.assertEqual(self.call(self.repo, "rev-parse", "HEAD").stdout.strip(), upstream)

    def test_pending_merge_reentry_is_recognized(self):
        self.local_release()
        self.upstream_change()
        first = rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)
        second = rd.reconcile_upstream(self.repo, ALLOWLIST, DAY)
        self.assertEqual(second["action"], "already_integrated")
        self.assertEqual(first["head"], second["head"])

    def test_noop_publisher_still_pushes_preexisting_local_commit(self):
        self.assert_noop_reentry(diverged=False)

    def test_noop_publisher_recovers_already_committed_divergence(self):
        self.assert_noop_reentry(diverged=True)

    def assert_noop_reentry(self, *, diverged):
        local = self.local_release()
        if diverged:
            self.upstream_change()
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"date": DAY, "slug": "example", "title": "Today", "webImageAssets": []}), encoding="utf-8")
        real_run = rd.run

        def fake_publisher(args, cwd, check=True):
            if args[0] == sys.executable:
                value = {"article": str(self.repo / ARTICLE), "status": "published", "webImageAssets": []} if "publish" in args else {}
                return subprocess.CompletedProcess(args, 0, json.dumps(value), "")
            return real_run(args, cwd, check=check)

        with patch.object(rd, "run", side_effect=fake_publisher), patch.object(rd, "verify_live"):
            result = rd.release(self.repo, manifest)
        self.assertEqual(result["staged_paths"], [])
        self.assertTrue(result["git_delivery"]["pushed"])
        self.assertTrue(rd.is_ancestor(self.repo, local, self.remote_head()))

    def test_global_staged_change_is_not_committed_or_unstaged(self):
        self.local_release()
        self.write(self.repo, "daily-art.txt", "user draft\n")
        self.call(self.repo, "add", "daily-art.txt")
        before = self.call(self.repo, "status", "--porcelain").stdout
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"date": DAY, "slug": "example", "title": "Today"}), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "unexpected dirty checkpoint path"):
            rd.release(self.repo, manifest)
        self.assertEqual(self.call(self.repo, "status", "--porcelain").stdout, before)
        self.assertEqual((self.repo / "daily-art.txt").read_text(), "user draft\n")

    def test_in_progress_merge_is_not_treated_as_release_checkpoint(self):
        self.local_release("local\n")
        self.upstream_change(ARTICLE, "remote\n")
        self.call(self.repo, "fetch", "origin", "main")
        self.assertNotEqual(self.call(self.repo, "merge", "origin/main", check=False).returncode, 0)
        before = self.call(self.repo, "status", "--porcelain").stdout
        with self.assertRaisesRegex(RuntimeError, "unfinished Git operation"):
            rd.verify_repo(self.repo, self.repo / "ip-object-workshop", allow_dirty=True)
        self.assertEqual(self.call(self.repo, "status", "--porcelain").stdout, before)
        self.assertTrue((self.repo / ".git/MERGE_HEAD").exists())

    def test_permission_push_rejection_is_not_retried(self):
        self.local_release()
        real_git = rd.git
        pushes = []

        def denied(repo, *args, **kwargs):
            if args and args[0] == "push":
                pushes.append(args)
                return subprocess.CompletedProcess(args, 1, "", "Permission denied (publickey).")
            return real_git(repo, *args, **kwargs)

        with patch.object(rd, "git", side_effect=denied):
            with self.assertRaisesRegex(RuntimeError, "failed after 1 attempt"):
                rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, lambda: None)
        self.assertEqual(len(pushes), 1)

    def test_validator_failure_stops_push_and_preserves_local_commit(self):
        local = self.local_release()
        remote = self.remote_head()

        def invalid():
            raise RuntimeError("site validation failed")

        with self.assertRaisesRegex(RuntimeError, "site validation failed"):
            rd.push_release_with_reconciliation(self.repo, ALLOWLIST, DAY, invalid)
        self.assertEqual(self.remote_head(), remote)
        self.assertEqual(self.call(self.repo, "rev-parse", "HEAD").stdout.strip(), local)


if __name__ == "__main__":
    unittest.main()
