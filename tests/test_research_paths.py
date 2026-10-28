#!/usr/bin/env python3
"""Tests for research_paths.py — the single authority for run output locations."""

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "research_paths.py"

sys.path.insert(0, str(SCRIPTS))
import research_paths  # noqa: E402


class SlugifyTopicTests(unittest.TestCase):
    def test_collapses_whitespace(self):
        self.assertEqual("PostgreSQL_vs_Supabase", research_paths.slugify_topic("PostgreSQL vs Supabase"))

    def test_keeps_cjk(self):
        self.assertEqual("城市更新政策", research_paths.slugify_topic("城市更新政策"))

    def test_mixed_language_keeps_both(self):
        self.assertEqual("PostgreSQL_与_Supabase_对比", research_paths.slugify_topic("PostgreSQL 与 Supabase 对比"))

    def test_strips_path_separators(self):
        # A topic containing separators must not be able to escape the container.
        slug = research_paths.slugify_topic("../../etc/passwd")
        self.assertNotIn("/", slug)
        self.assertNotIn("\\", slug)
        self.assertEqual("etc_passwd", slug)

    def test_strips_illegal_windows_chars(self):
        slug = research_paths.slugify_topic('a<b>c:d"e|f?g*h')
        for char in '<>:"|?*':
            self.assertNotIn(char, slug)

    def test_trims_edge_junk(self):
        self.assertEqual("topic", research_paths.slugify_topic("  ..topic..  "))

    def test_truncates_long_topics(self):
        slug = research_paths.slugify_topic("x" * 200)
        self.assertLessEqual(len(slug), 60)

    def test_empty_topic_falls_back(self):
        self.assertEqual("untitled_研究_20261028", research_paths.build_folder_name("   ", datetime(2026, 10, 28)))


class BuildFolderNameTests(unittest.TestCase):
    def test_composes_chinese_suffix_and_date(self):
        name = research_paths.build_folder_name("PostgreSQL vs Supabase", datetime(2026, 10, 28))
        self.assertEqual("PostgreSQL_vs_Supabase_研究_20261028", name)

    def test_chinese_topic(self):
        name = research_paths.build_folder_name("城市更新政策", datetime(2026, 10, 28))
        self.assertEqual("城市更新政策_研究_20261028", name)


class ResolveRunDirTests(unittest.TestCase):
    def test_places_run_under_research_container(self):
        with tempfile.TemporaryDirectory() as base:
            path = research_paths.resolve_run_dir("quantum computing", base=base, date=datetime(2026, 10, 28))
            self.assertEqual(Path(base) / "research" / "quantum_computing_研究_20261028", path)

    def test_is_relative_to_base_not_home(self):
        with tempfile.TemporaryDirectory() as base:
            path = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28))
            self.assertTrue(str(path).startswith(str(Path(base).resolve())), path)

    def test_create_makes_directory(self):
        with tempfile.TemporaryDirectory() as base:
            path = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28), create=True)
            self.assertTrue(path.is_dir())

    def test_collision_adds_numeric_suffix(self):
        with tempfile.TemporaryDirectory() as base:
            first = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28), create=True)
            second = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28), create=True)
            third = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28), create=True)
            self.assertEqual("topic_研究_20261028", first.name)
            self.assertEqual("topic_研究_20261028_2", second.name)
            self.assertEqual("topic_研究_20261028_3", third.name)

    def test_without_create_is_idempotent(self):
        with tempfile.TemporaryDirectory() as base:
            a = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28))
            b = research_paths.resolve_run_dir("topic", base=base, date=datetime(2026, 10, 28))
            self.assertEqual(a, b)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.returncode, result.stdout, result.stderr

    def test_resolve_emits_json(self):
        with tempfile.TemporaryDirectory() as base:
            code, out, _ = self.run_cli(
                "resolve", "--topic", "城市更新政策", "--base", base, "--date", "20261028"
            )
            self.assertEqual(0, code)
            payload = json.loads(out)
            self.assertEqual("ok", payload["status"])
            self.assertTrue(payload["relative"].startswith("research/"))
            self.assertIn("城市更新政策_研究_20261028", payload["relative"])

    def test_resolve_create_creates_directory(self):
        with tempfile.TemporaryDirectory() as base:
            code, out, _ = self.run_cli(
                "resolve", "--topic", "topic", "--base", base, "--date", "20261028", "--create"
            )
            self.assertEqual(0, code)
            self.assertTrue(Path(json.loads(out)["dir"]).is_dir())

    def test_check_accepts_conforming_directory(self):
        with tempfile.TemporaryDirectory() as base:
            run_dir = Path(base) / "research" / "topic_研究_20261028"
            run_dir.mkdir(parents=True)
            code, out, _ = self.run_cli("check", "--dir", str(run_dir))
            self.assertEqual(0, code)
            self.assertEqual("pass", json.loads(out)["status"])

    def test_check_rejects_missing_container(self):
        with tempfile.TemporaryDirectory() as base:
            run_dir = Path(base) / "topic_研究_20261028"
            run_dir.mkdir()
            code, out, _ = self.run_cli("check", "--dir", str(run_dir))
            self.assertNotEqual(0, code)
            payload = json.loads(out)
            self.assertEqual("fail", payload["status"])
            self.assertTrue(any("research/" in p for p in payload["problems"]))

    def test_check_rejects_wrong_suffix(self):
        with tempfile.TemporaryDirectory() as base:
            run_dir = Path(base) / "research" / "topic_Research_20261028"
            run_dir.mkdir(parents=True)
            code, out, _ = self.run_cli("check", "--dir", str(run_dir))
            self.assertNotEqual(0, code)
            self.assertIn("研究", json.loads(out)["problems"][0])


if __name__ == "__main__":
    unittest.main()
