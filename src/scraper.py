"""Collect accepted papers with explicit, inspectable classification evidence."""
import argparse
import re
from pathlib import Path
from urllib.parse import urljoin

from paper_agent.storage import ValidationError


def _value(content, key, default=''):
    value = content.get(key, default)
    return value.get('value', default) if isinstance(value, dict) else value


def fetch_top_papers(venue_id, limit=10, category='oral', client=None):
    """Filter accepted papers; never infer awards from collection order or title."""
    if limit < 1:
        raise ValidationError('limit must be positive')
    if category not in {'accepted', 'oral', 'spotlight', 'best-paper'}:
        raise ValidationError('Unsupported category')
    if client is None:
        import openreview
        client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')
    submissions = client.get_all_notes(content={'venueid': venue_id}, details='directReplies')
    papers = []
    pattern = {'oral': r'\boral\b', 'spotlight': r'\bspotlight\b',
               'best-paper': r'\bbest[ -]paper\b'}.get(category)
    for note in sorted(submissions, key=lambda n: n.id):
        if _value(note.content, 'venueid') != venue_id:
            continue
        basis = []
        for key in ('venue', 'decision', 'award'):
            value = _value(note.content, key)
            if isinstance(value, str) and value:
                basis.append({'field': f'submission.content.{key}', 'value': value})
        for reply in (getattr(note, 'details', None) or {}).get('directReplies', []):
            content = reply.get('content', {})
            invitations = ' '.join(reply.get('invitations', []))
            if 'Decision' in invitations:
                decision = _value(content, 'decision')
                if decision:
                    basis.append({'field': f"reply:{reply.get('id', 'unknown')}.decision", 'value': decision})
        matching = basis if pattern is None else [b for b in basis
            if re.search(pattern, str(b['value']), re.I) and not re.search(
                r'\b(?:not|no|non|reject(?:ed)?)\b', str(b['value']), re.I)]
        if pattern and not matching:
            continue
        # Only use a PDF attachment that the actual note advertises.
        pdf = _value(note.content, 'pdf')
        if not isinstance(pdf, str) or not pdf:
            continue
        papers.append({'id': note.id, 'number': note.number,
                       'title': _value(note.content, 'title', 'Untitled'),
                       'pdf_url': urljoin('https://openreview.net', pdf),
                       'venue': venue_id, 'category': category,
                       'acceptance_basis': {'field': 'content.venueid', 'value': venue_id},
                       'classification_basis': matching,
                       'source_url': f'https://openreview.net/forum?id={note.id}'})
        if len(papers) >= limit:
            break
    return papers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--venue', required=True, help='Explicit OpenReview venue/year ID')
    parser.add_argument('--category', choices=['accepted', 'oral', 'spotlight', 'best-paper'], default='oral')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--out', type=Path, default=Path('data/paper_metadata.json'))
    args = parser.parse_args()
    try:
        papers = fetch_top_papers(args.venue, args.limit, args.category)
        if not papers:
            raise ValidationError('No papers have the requested classification evidence; no output written')
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('x', encoding='utf-8') as f:
            import json
            json.dump(papers, f, ensure_ascii=False, indent=2)
        print(f'Saved {len(papers)} classified papers to {args.out}')
        return 0
    except (ValidationError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
