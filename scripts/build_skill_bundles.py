#!/usr/bin/env python3
"""Build self-contained, readable skill bundles from the canonical Python sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/paper_agent'
DEST = ROOT / 'skills'
RUNNER = '''#!/usr/bin/env python3
"""Run the bundled Paper-Agent tools from any working directory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'runtime'))
try:
    from paper_agent.cli import main
except ModuleNotFoundError as exc:
    if exc.name in {'yaml', 'fitz'}:
        raise SystemExit('Missing dependency: install scripts/requirements.txt in a Python virtual environment.') from None
    raise

if __name__ == '__main__':
    raise SystemExit(main())
'''


def expected_files():
    sources = {str(p.relative_to(SOURCE)): p.read_bytes() for p in SOURCE.glob('*.py')}
    documents = {str(p.relative_to(SOURCE)): p.read_bytes() for p in (SOURCE / 'skills').rglob('*.md')}
    result = {}
    for skill in sorted((SOURCE / 'skills').iterdir()):
        if not (skill / 'SKILL.md').is_file():
            continue
        prefix = skill.name + '/'
        for path in skill.rglob('*.md'):
            result[prefix + str(path.relative_to(skill))] = path.read_bytes()
        result[prefix + 'scripts/paper_agent.py'] = RUNNER.encode()
        result[prefix + 'scripts/requirements.txt'] = b'PyYAML>=6,<7\nPyMuPDF>=1.24,<2\n'
        for relative, data in {**sources, **documents}.items():
            result[prefix + 'scripts/runtime/paper_agent/' + relative] = data
    return result


def build(check=False):
    expected = expected_files()
    present = {str(p.relative_to(DEST)) for p in DEST.rglob('*')
               if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'} if DEST.exists() else set()
    changed = [name for name, data in expected.items()
               if not (DEST / name).is_file() or (DEST / name).read_bytes() != data]
    extra = sorted(present - expected.keys())
    if check:
        if changed or extra:
            raise SystemExit('Stale bundles. Run python3 scripts/build_skill_bundles.py. '
                             f'Changed/missing: {changed}; unexpected: {extra}')
    else:
        if extra:
            raise SystemExit(f'Unexpected bundle files preserved; inspect before regenerating: {extra}')
        for name, data in expected.items():
            path = DEST / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return {'skills': len([p for p in (SOURCE / 'skills').glob('*/SKILL.md')]),
            'files': len(expected), 'state': 'current' if check else 'built',
            'sha256': hashlib.sha256(json.dumps({k: hashlib.sha256(v).hexdigest()
                                               for k, v in sorted(expected.items())}, sort_keys=True).encode()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    print(json.dumps(build(parser.parse_args().check), indent=2))
