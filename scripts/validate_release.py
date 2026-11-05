#!/usr/bin/env python3
"""Produce reproducible engineering evidence, separate from live model evaluation."""
import argparse
import contextlib
import copy
import hashlib
import io
import json
import platform
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from paper_agent import __version__
from paper_agent.storage import ValidationError, read_json, write_json
from paper_agent.workflow import apply_response, check_run, prepare, validate_response


def fingerprint():
    paths = []
    for folder in ('src', 'tests', 'examples/revision', 'scripts'):
        paths.extend(p for p in (ROOT / folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix in {'.py', '.md', '.json', '.csv', '.bib', '.txt'})
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def validate():
    subprocess.run([sys.executable, str(ROOT / 'scripts/build_skill_bundles.py'), '--check'], check=True,
                   capture_output=True)
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        tests = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
    report = {'schema_version': 1, 'date_utc': datetime.now(timezone.utc).isoformat(),
              'version': __version__, 'python': platform.python_version(), 'platform': platform.system(),
              'source_tree_sha256': fingerprint(),
              'unit_tests': {'run': tests.testsRun, 'failures': len(tests.failures),
                             'errors': len(tests.errors), 'skipped': len(tests.skipped)},
              'interpretation': 'Engineering validation only. No acceptance-rate, writing-quality, '
                                'scientific-correctness, or unassisted-model improvement claim.'}
    fixture = ROOT / 'examples/revision'
    with tempfile.TemporaryDirectory(prefix='paper-agent-validation-') as temporary:
        root = Path(temporary)
        run = root / 'run'
        prepare(fixture / 'paper.md', run, fixture / 'results.csv', fixture / 'references.bib')
        material = read_json(run / 'materials.json')
        text = (run / 'manuscript.txt').read_text()
        answer = read_json(fixture / 'response_fixture.json')
        answer['bundle_id'] = material['bundle_id']
        variants = {
            'unknown_evidence': lambda r: r['edits'][0].update(evidence_ids=['exp:missing']),
            'unprovided_number': lambda r: r['edits'][0].update(replacement='Accuracy is 99%.'),
            'new_unresolved_citation': lambda r: r['edits'][0].update(replacement='See [@missing].'),
            'stale_original': lambda r: r['edits'][0].update(original='Stale manuscript text'),
            'overlapping_edits': lambda r: r['edits'].append(copy.deepcopy(r['edits'][0]) | {'id': 'overlap'}),
            'wrong_bundle': lambda r: r.update(bundle_id='different'),
            'incomplete_coverage': lambda r: r.update(reviewed_chunks=[]),
            'not_run_as_completed_evidence': lambda r: r['edits'][0].update(evidence_ids=['exp:robustness']),
            'metadata_only_scientific_support': lambda r: r['claim_reviews'][2].update(status='supported'),
        }
        rejected = []
        accepted = []
        for name, change in variants.items():
            response = copy.deepcopy(answer)
            change(response)
            try:
                validate_response(response, material, text)
            except ValidationError:
                rejected.append(name)
            else:
                accepted.append(name)
        report['invalid_response_scenarios'] = {'tested': len(variants), 'rejected': len(rejected),
                                                'rejected_cases': rejected, 'unexpectedly_accepted': accepted}
        response_file = root / 'response.json'
        write_json(response_file, answer)
        original_bytes = (fixture / 'paper.md').read_bytes()
        apply_response(run, response_file)
        check = check_run(run)
        report['synthetic_revision_replay'] = {
            'response_provenance': 'pre_authored_host_agent_fixture',
            'original_mechanical_findings': len(check['original']['findings']),
            'revised_mechanical_findings': len(check['revised']['findings']),
            'applied_edits': len(answer['edits']),
            'pending_suggestions_retained': len(check['agent_review']['pending_suggestions']),
            'original_bytes_preserved': (fixture / 'paper.md').read_bytes() == original_bytes,
            'scientific_validation': check['scientific_validation']}
    report['status'] = 'passed' if tests.wasSuccessful() and not accepted else 'failed'
    if not tests.wasSuccessful():
        print(stream.getvalue(), file=sys.stderr)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = validate()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.out, report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)
