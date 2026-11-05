"""Extract complete PDF text with page/line provenance, without claiming layout fidelity."""
import argparse
from pathlib import Path

from paper_agent.materials import load_paper
from paper_agent.storage import ValidationError, digest, json_text


def pdf_to_markdown(pdf_path, md_path):
    pdf_path, md_path = Path(pdf_path), Path(md_path)
    provenance_path = md_path.with_suffix('.source.json')
    if md_path.exists() or provenance_path.exists():
        raise ValidationError(f'Output already exists: {md_path}')
    text, pages, warnings = load_paper(pdf_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    provenance = {'pdf_path': str(pdf_path.resolve()), 'pdf_sha256': digest(pdf_path.read_bytes()),
                  'text_sha256': digest(text), 'pages': pages, 'warnings': warnings,
                  'classification': 'unknown; consult collection metadata'}
    with md_path.open('x', encoding='utf-8') as stream:
        stream.write(text)
    with provenance_path.open('x', encoding='utf-8') as stream:
        stream.write(json_text(provenance))
    return str(md_path)


def process_all_pdfs(pdf_dir='data/pdfs', md_dir='data/markdown'):
    pdf_dir, md_dir = Path(pdf_dir), Path(md_dir)
    if not pdf_dir.is_dir():
        raise ValidationError(f'PDF directory does not exist: {pdf_dir}; run downloader.py first')
    pdfs = sorted(pdf_dir.glob('*.pdf'))
    if not pdfs:
        raise ValidationError(f'No PDFs in {pdf_dir}')
    return [pdf_to_markdown(p, md_dir / f'{p.stem}.md') for p in pdfs]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--pdf-dir', default='data/pdfs')
    parser.add_argument('--md-dir', default='data/markdown')
    args = parser.parse_args()
    try:
        if args.pdf:
            if not args.out:
                parser.error('--pdf requires --out')
            print(pdf_to_markdown(args.pdf, args.out))
        else:
            if args.out:
                parser.error('--out requires --pdf')
            print('\n'.join(process_all_pdfs(args.pdf_dir, args.md_dir)))
    except (ValidationError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')
