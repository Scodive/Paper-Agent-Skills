import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'examples/revision'


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='paper-agent-skill-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env.pop('PYTHONPATH', None)

    def run_cli(self, runner, *args):
        return subprocess.run([sys.executable, str(runner), *map(str, args)], cwd=self.root,
                              env=self.env, capture_output=True, text=True, check=True)

    def copy_bundle(self, name):
        destination = self.root / 'installed' / name
        shutil.copytree(ROOT / 'skills' / name, destination,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        return destination / 'scripts/paper_agent.py'

    def test_generated_bundles_match_canonical_sources(self):
        subprocess.run([sys.executable, str(ROOT / 'scripts/build_skill_bundles.py'), '--check'],
                       capture_output=True, check=True)

    def test_each_installed_bundle_runs_outside_the_source_checkout(self):
        for name in ('academic-paper-writing', 'rebuttal-writing', 'presentation-slides'):
            with self.subTest(skill=name):
                result = self.run_cli(self.copy_bundle(name), 'validate-skills')
                self.assertEqual(len(json.loads(result.stdout)['skills']), 3)

    def test_standalone_revision_produces_a_portable_task_and_validated_outputs(self):
        runner = self.copy_bundle('academic-paper-writing')
        run = self.root / 'review with spaces'
        self.run_cli(runner, 'prepare', '--paper', FIXTURE / 'paper.md',
                     '--experiments', FIXTURE / 'results.csv', '--references', FIXTURE / 'references.bib',
                     '--out', run)
        task = (run / 'agent_task.md').read_text()
        self.assertIn(str(runner), task)
        self.assertNotIn('python3 src/main.py apply', task)
        response = json.loads((FIXTURE / 'response_fixture.json').read_text())
        response['bundle_id'] = json.loads((run / 'manifest.json').read_text())['bundle_id']
        response_path = run / 'response.json'
        response_path.write_text(json.dumps(response))
        result = json.loads(self.run_cli(runner, 'apply', '--run', run, '--response', response_path).stdout)
        self.assertEqual(result['edits'], 5)
        report = json.loads(self.run_cli(runner, 'check', '--run', run).stdout)
        self.assertEqual(len(report['agent_review']['pending_suggestions']), 2)
        self.assertEqual(report['scientific_validation'], 'not_established')
        self.assertIn('93% accuracy', (run / 'results/revised.md').read_text())


if __name__ == '__main__':
    unittest.main()
