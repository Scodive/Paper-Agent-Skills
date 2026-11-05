#!/usr/bin/env python3
"""Replay a checked-in host-agent review; this is not an automatic model invocation."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from paper_agent.storage import read_json, write_json
from paper_agent.workflow import apply_response, check_run, prepare


def demo(out):
    here = Path(__file__).parent
    prepare(here / 'paper.md', out, here / 'results.csv', here / 'references.bib')
    response = read_json(here / 'response_fixture.json')
    response['bundle_id'] = read_json(Path(out) / 'manifest.json')['bundle_id']
    dest = Path(out) / 'response.json'
    write_json(dest, response)
    result = apply_response(out, dest)
    checked = check_run(out)
    result['test_type'] = 'replay_of_pre_authored_host_agent_response'
    result['pending_agent_issues'] = len(checked['agent_review']['pending_suggestions'])
    print(__import__('json').dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    demo(parser.parse_args().out)
