#!/usr/bin/env python3
"""Record a completed local DSH exercise without publishing credentials or raw logs."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from paper_agent.storage import read_json, write_json
from paper_agent.workflow import check_run
from build_skill_bundles import expected_files


def record(run_root, installed_skills, out):
    run_root, installed_skills = Path(run_root), Path(installed_skills)
    process = read_json(run_root / 'process-result.json')
    events = [json.loads(line) for line in (run_root / 'events.jsonl').read_text().splitlines() if line.strip()]
    finals = [e for e in events if e.get('type') == 'final']
    if process['exit_code'] != 0 or not finals or finals[-1].get('reason', {}).get('kind') != 'completed':
        raise SystemExit('DSH run did not complete; no success receipt written')
    calls = {e['callId']: e['input']['name'] for e in events
             if e.get('type') == 'tool_call' and e.get('tool') == 'skill'}
    loaded = sorted({calls[e['callId']] for e in events if e.get('type') == 'tool_result'
                     and e.get('callId') in calls and e.get('status') == 'completed'
                     and '<skill_content' in str(e.get('result', ''))})
    expected = expected_files()
    for relative, data in expected.items():
        path = installed_skills / relative
        if not path.is_file() or path.read_bytes() != data:
            raise SystemExit(f'Tested installation differs from current bundle: {relative}')
    if set(loaded) != {'academic-paper-writing', 'rebuttal-writing', 'presentation-slides'}:
        raise SystemExit('Not all three skills loaded successfully')
    case = run_root / 'case'
    check = check_run(case / 'review')
    material = read_json(case / 'review/materials.json')
    source_inputs = read_json(case / 'review/manifest.json')['inputs']
    for item in source_inputs:
        if item['role'] in {'paper', 'experiments', 'references'}:
            fixture_name = {'paper':'paper.md', 'experiments':'results.csv', 'references':'references.bib'}[item['role']]
            if item['sha256'] != hashlib.sha256((ROOT / 'examples/revision' / fixture_name).read_bytes()).hexdigest():
                raise SystemExit('DSH exercise inputs differ from the documented synthetic fixtures')
    response = read_json(case / 'review/response.json')
    if '/Users/' in json.dumps(response) or '/home/' in json.dumps(response):
        raise SystemExit('Response contains local paths; redact before publishing')
    result = {'schema_version': 1, 'status': 'passed',
              'test_type': 'single_live_dsh_host_agent_revision',
              'dsh_version': process['dsh_version'], 'provider': process['provider'], 'model': process['model'],
              'process_exit_code': 0, 'terminal_reason': 'completed', 'elapsed_seconds': process['elapsed_seconds'],
              'skills_loaded': loaded, 'installed_bundle_files_verified': len(expected),
              'reviewed_chunks': check['agent_review']['reviewed_chunks'],
              'total_chunks': check['agent_review']['total_chunks'],
              'original_mechanical_findings': len(check['original']['findings']),
              'revised_mechanical_findings': len(check['revised']['findings']),
              'applied_edits': check['agent_review']['edits'],
              'pending_suggestions_retained': len(check['agent_review']['pending_suggestions']),
              'independent_artifact_recheck': 'passed', 'scientific_validation': 'not_established',
              'event_log_sha256': hashlib.sha256((run_root / 'events.jsonl').read_bytes()).hexdigest(),
              'limitations': ['One synthetic case and one live model run; not a statistical benchmark.',
                             'Only academic-paper-writing executed a complete generation workflow.',
                             'Rebuttal and slides were discovered and loaded, not behaviorally evaluated.',
                             'No unassisted-model baseline, acceptance-rate measurement or experiment reproduction.',
                             'Raw account credentials and session logs are not included in this public receipt.']}
    write_json(out, result)
    write_json(Path(out).with_name('dsh-response.json'), response)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--installed-skills', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    record(args.run, args.installed_skills, args.out)
