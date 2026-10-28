#!/usr/bin/env python3
"""Smoke tests for citation_manager.py CLI."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

SCRIPT = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'citation_manager.py')


def run_cm(*args: str) -> dict:
    """Run citation_manager.py with args, return parsed JSON from stdout."""
    result = subprocess.run(
        [sys.executable, SCRIPT, *args],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f'Exit {result.returncode}: {result.stderr}')
    return json.loads(result.stdout) if result.stdout.strip().startswith(('{', '[')) else result.stdout


class TestInitRun(unittest.TestCase):
    def test_creates_manifest_and_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            out = run_cm('init-run', '--out-dir', d, '--query', 'test question', '--mode', 'deep')
            self.assertEqual(out['status'], 'ok')

            # Manifest exists and has correct fields
            manifest = json.load(open(os.path.join(d, 'run_manifest.json')))
            self.assertEqual(manifest['version'], '3.0.0')
            self.assertEqual(manifest['query'], 'test question')
            self.assertEqual(manifest['mode'], 'deep')
            self.assertIsNotNone(manifest['started_at'])
            self.assertIsNone(manifest['finished_at'])
            self.assertEqual(manifest['artifact_paths']['sources'], 'sources.jsonl')

            # Empty JSONL files exist
            for name in ('sources.jsonl', 'evidence.jsonl', 'claims.jsonl'):
                path = os.path.join(d, name)
                self.assertTrue(os.path.exists(path), f'{name} missing')
                self.assertEqual(os.path.getsize(path), 0)


class TestRegisterSource(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        run_cm('init-run', '--out-dir', self.tmpdir, '--query', 'test')

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_and_dedup(self):
        src = json.dumps({
            'raw_url': 'https://arxiv.org/abs/2305.14251',
            'title': 'FActScore',
            'source_type': 'academic',
            'year': '2023',
        })
        out1 = run_cm('register-source', '--json', src, '--dir', self.tmpdir)
        self.assertEqual(out1['status'], 'registered')
        self.assertEqual(len(out1['source_id']), 16)
        self.assertTrue(out1['canonical_locator'].startswith('arxiv:'))

        # Same URL -> duplicate
        out2 = run_cm('register-source', '--json', src, '--dir', self.tmpdir)
        self.assertEqual(out2['status'], 'duplicate')
        self.assertEqual(out2['source_id'], out1['source_id'])

    def test_doi_canonicalization(self):
        src = json.dumps({
            'raw_url': 'https://doi.org/10.1038/s41586-023-06745-9',
            'title': 'Some Nature paper',
        })
        out = run_cm('register-source', '--json', src, '--dir', self.tmpdir)
        self.assertTrue(out['canonical_locator'].startswith('doi:10.1038/'))

    def test_url_normalization(self):
        src1 = json.dumps({
            'raw_url': 'https://Example.Com/article?utm_source=google&id=42',
            'title': 'Test',
        })
        src2 = json.dumps({
            'raw_url': 'https://example.com/article?id=42&utm_medium=email',
            'title': 'Test duplicate',
        })
        out1 = run_cm('register-source', '--json', src1, '--dir', self.tmpdir)
        out2 = run_cm('register-source', '--json', src2, '--dir', self.tmpdir)
        # Both should resolve to same canonical locator -> same source_id
        self.assertEqual(out1['source_id'], out2['source_id'])
        self.assertEqual(out2['status'], 'duplicate')


class TestAssignDisplayNumbers(unittest.TestCase):
    def test_assigns_in_order(self):
        with tempfile.TemporaryDirectory() as d:
            run_cm('init-run', '--out-dir', d, '--query', 'test')

            for i, url in enumerate(['https://a.com/1', 'https://b.com/2', 'https://c.com/3']):
                run_cm('register-source', '--json', json.dumps({
                    'raw_url': url, 'title': f'Source {i+1}',
                }), '--dir', d)

            mapping = run_cm('assign-display-numbers', '--dir', d)
            self.assertEqual(len(mapping), 3)
            # Values should be 1, 2, 3
            self.assertEqual(sorted(mapping.values()), [1, 2, 3])


class TestExportBibliography(unittest.TestCase):
    def test_markdown_export(self):
        with tempfile.TemporaryDirectory() as d:
            run_cm('init-run', '--out-dir', d, '--query', 'test')
            run_cm('register-source', '--json', json.dumps({
                'raw_url': 'https://arxiv.org/abs/2305.14251',
                'title': 'FActScore',
                'authors': ['Min, S.', 'Krishna, K.'],
                'year': '2023',
                'source_type': 'academic',
            }), '--dir', d)

            out = run_cm('export-bibliography', '--dir', d, '--style', 'markdown')
            self.assertIn('[1]', out)
            self.assertIn('FActScore', out)
            self.assertIn('Min, S. & Krishna, K.', out)

    def test_json_export(self):
        with tempfile.TemporaryDirectory() as d:
            run_cm('init-run', '--out-dir', d, '--query', 'test')
            run_cm('register-source', '--json', json.dumps({
                'raw_url': 'https://example.com/paper',
                'title': 'Test Paper',
            }), '--dir', d)

            out = run_cm('export-bibliography', '--dir', d, '--style', 'json')
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]['display_number'], 1)
            self.assertEqual(out[0]['title'], 'Test Paper')


class TestCanonicalization(unittest.TestCase):
    """Unit tests for canonicalize_locator without running the CLI."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        from citation_manager import canonicalize_locator, compute_source_id
        cls.canonicalize = staticmethod(canonicalize_locator)
        cls.compute_id = staticmethod(compute_source_id)

    def test_doi_from_url(self):
        canonicalize_locator = self.canonicalize
        self.assertEqual(
            canonicalize_locator('https://doi.org/10.1038/s41586-023-06745-9'),
            'doi:10.1038/s41586-023-06745-9',
        )
        self.assertEqual(
            canonicalize_locator('https://dx.doi.org/10.1234/test.'),
            'doi:10.1234/test',
        )

    def test_arxiv_from_url(self):
        canonicalize_locator = self.canonicalize
        self.assertEqual(
            canonicalize_locator('https://arxiv.org/abs/2305.14251v2'),
            'arxiv:2305.14251v2',
        )
        self.assertEqual(
            canonicalize_locator('arxiv:2401.15884'),
            'arxiv:2401.15884',
        )

    def test_url_strips_tracking(self):
        canonicalize_locator = self.canonicalize
        result = canonicalize_locator('https://Example.Com/page?utm_source=x&key=val')
        self.assertNotIn('utm_source', result)
        self.assertIn('key=val', result)
        self.assertTrue(result.startswith('https://example.com'))

    def test_url_strips_fragment(self):
        canonicalize_locator = self.canonicalize
        result = canonicalize_locator('https://example.com/page#section')
        self.assertNotIn('#section', result)

    def test_url_strips_trailing_slash(self):
        canonicalize_locator = self.canonicalize
        result = canonicalize_locator('https://example.com/page/')
        self.assertFalse(result.endswith('/'))


class TestRunDirectoryConvention(unittest.TestCase):
    """The run folder name is resolved here, so it is tested here."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
        import citation_manager
        cls.cm = citation_manager

    def test_slug_collapses_whitespace(self):
        self.assertEqual('PostgreSQL_vs_Supabase', self.cm.slugify_topic('PostgreSQL vs Supabase'))

    def test_slug_keeps_cjk(self):
        self.assertEqual('城市更新政策', self.cm.slugify_topic('城市更新政策'))

    def test_slug_keeps_both_languages(self):
        self.assertEqual('PostgreSQL_与_Supabase_对比', self.cm.slugify_topic('PostgreSQL 与 Supabase 对比'))

    def test_slug_cannot_escape_container(self):
        slug = self.cm.slugify_topic('../../etc/passwd')
        self.assertNotIn('/', slug)
        self.assertNotIn('\\', slug)
        self.assertEqual('etc_passwd', slug)

    def test_slug_strips_windows_illegal_chars(self):
        slug = self.cm.slugify_topic('a<b>c:d"e|f?g*h')
        for char in '<>:"|?*':
            self.assertNotIn(char, slug)

    def test_slug_truncates(self):
        self.assertLessEqual(len(self.cm.slugify_topic('x' * 200)), 60)

    def test_resolve_places_run_under_research(self):
        with tempfile.TemporaryDirectory() as base:
            path = self.cm.resolve_run_dir('quantum computing', base=base, date=datetime(2026, 10, 28))
            self.assertEqual(Path(base) / 'research' / 'quantum_computing_研究_20261028', path)

    def test_resolve_collision_adds_suffix(self):
        with tempfile.TemporaryDirectory() as base:
            first = self.cm.resolve_run_dir('topic', base=base, date=datetime(2026, 10, 28), create=True)
            second = self.cm.resolve_run_dir('topic', base=base, date=datetime(2026, 10, 28), create=True)
            self.assertEqual('topic_研究_20261028', first.name)
            self.assertEqual('topic_研究_20261028_2', second.name)

    def test_check_accepts_conforming_dir(self):
        with tempfile.TemporaryDirectory() as base:
            run_dir = Path(base) / 'research' / 'topic_研究_20261028'
            run_dir.mkdir(parents=True)
            self.assertEqual([], self.cm.check_run_dir(run_dir))

    def test_check_rejects_missing_container(self):
        with tempfile.TemporaryDirectory() as base:
            run_dir = Path(base) / 'topic_研究_20261028'
            run_dir.mkdir()
            problems = self.cm.check_run_dir(run_dir)
            self.assertTrue(any('research/' in p for p in problems))

    def test_check_rejects_english_suffix(self):
        with tempfile.TemporaryDirectory() as base:
            run_dir = Path(base) / 'research' / 'topic_Research_20261028'
            run_dir.mkdir(parents=True)
            self.assertTrue(any('研究' in p for p in self.cm.check_run_dir(run_dir)))

    def test_init_run_resolves_dir_from_query(self):
        with tempfile.TemporaryDirectory() as base:
            cwd = os.getcwd()
            os.chdir(base)
            try:
                out = run_cm('init-run', '--query', '城市更新政策', '--mode', 'standard')
            finally:
                os.chdir(cwd)
            self.assertTrue(out['dir'].endswith(os.path.join('research', '城市更新政策_研究_' + datetime.now().strftime('%Y%m%d'))))
            self.assertTrue(os.path.isdir(out['dir']))

    def test_init_run_requires_dir_or_query(self):
        result = subprocess.run(
            [sys.executable, SCRIPT, 'init-run'],
            capture_output=True, text=True,
        )
        self.assertNotEqual(0, result.returncode)


if __name__ == '__main__':
    unittest.main()
