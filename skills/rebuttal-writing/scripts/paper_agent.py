#!/usr/bin/env python3
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
