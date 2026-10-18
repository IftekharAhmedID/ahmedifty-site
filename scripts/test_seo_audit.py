"""Offline checks for audit identity matching and HTML validation inputs."""
import unittest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from seo_audit import Page, identity


class AuditTests(unittest.TestCase):
    def test_cli_rejects_evidence_inside_repository(self):
        repo = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, str(repo / 'scripts/seo_audit.py'),
                                 '--output-dir', str(repo / 'public/private-audit')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((repo / 'public/private-audit').exists())

    def test_cli_preserves_existing_measurements(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'run.json'
            path.write_text('{"existing": true}')
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('seo_audit.py')),
                                     '--output-dir', folder], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(path.read_text()), {'existing': True})

    def test_namesakes_and_lookalike_hosts_are_not_matches(self):
        self.assertEqual(identity(None), '')
        self.assertEqual(identity('https://['), '')
        self.assertEqual(identity('https://uk.linkedin.com/in/iftekhar-ahmed-/'), 'linkedin')
        self.assertEqual(identity('https://au.linkedin.com/in/iftekhar-ahmed-ia'), '')
        self.assertEqual(identity('https://evillinkedin.com/in/iftekhar-ahmed-'), '')
        self.assertEqual(identity('https://ahmedifty.com.attacker.example/'), '')
        self.assertEqual(identity('https://scholar.google.com/citations?user=r1WxofgAAAAJ'), '')
        self.assertEqual(identity('https://scholar.google.com/citations?hl=en&user=drQ6MO4AAAAJ'), 'scholar')

    def test_canonical_robots_nested_heading_and_json_are_read(self):
        p = Page()
        p.feed('<title>A &amp; B</title><link rel="canonical" href="https://ahmedifty.com/">'
               '<meta name="robots" content="NOINDEX"><h1><a href="/">Name</a></h1>'
               '<h2 id="results">Results</h2><script type="application/ld+json">{"@type":"Person"}</script>')
        self.assertEqual(p.title, 'A & B')
        self.assertEqual(p.h1, ['Name'])
        self.assertEqual(p.canonicals, ['https://ahmedifty.com/'])
        self.assertEqual(p.robots, ['noindex'])
        self.assertIn('results', p.ids)
        self.assertEqual(p.jsonld, [{'@type': 'Person'}])

    def test_invalid_json_and_duplicate_headings_are_observable(self):
        p = Page()
        p.feed('<h1>One</h1><h1>Two</h1><script type="application/ld+json">invalid</script>')
        self.assertEqual(len(p.h1), 2)
        self.assertEqual(len(p.json_errors), 1)


if __name__ == '__main__':
    unittest.main()
