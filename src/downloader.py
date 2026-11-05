"""Download complete PDF attachments with timeouts and atomic cache publication."""
import argparse
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from paper_agent.storage import ValidationError, read_json


def _valid_pdf(path):
    with Path(path).open('rb') as stream:
        if stream.read(5) != b'%PDF-':
            return False
    import fitz
    try:
        with fitz.open(path) as document:
            return document.page_count > 0 and not document.needs_pass
    except (RuntimeError, ValueError, OSError):
        return False


def download_pdfs(metadata_file='data/paper_metadata.json', output_dir='data/pdfs', max_bytes=100_000_000):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    papers = read_json(metadata_file)
    if not isinstance(papers, list):
        raise ValidationError('Paper metadata must be a list')
    downloaded = []
    errors = []
    for paper in papers:
        temp_path = None
        try:
            key = paper['id']
            if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', key):
                raise ValidationError('Invalid OpenReview paper id')
            title = re.sub(r'[^\w.-]+', '_', paper['title'])[:50]
            target = output_dir / f'{key}_{title}.pdf'
            if target.exists():
                if not _valid_pdf(target):
                    raise ValidationError(f'Existing cache is invalid; choose a new directory: {target}')
                downloaded.append(str(target))
                continue
            url = paper['pdf_url']
            if urlparse(url).scheme not in {'https', 'http'}:
                raise ValidationError('PDF URL must be HTTP(S)')
            with requests.get(url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(dir=output_dir, prefix='.download-', delete=False) as stream:
                    temp_path = Path(stream.name)
                    count = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        count += len(chunk)
                        if count > max_bytes:
                            raise ValidationError('PDF exceeds download size limit')
                        stream.write(chunk)
                if not _valid_pdf(temp_path):
                    raise ValidationError('Response is not a PDF or has no readable PDF pages')
                # A hard link publishes without replacing a concurrently created file.
                os.link(temp_path, target)
                downloaded.append(str(target))
        except (OSError, ValueError, KeyError, TypeError, requests.RequestException) as exc:
            errors.append(f"{paper.get('id', 'unknown') if isinstance(paper, dict) else 'unknown'}: {exc}")
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
    if errors:
        raise ValidationError('Some PDFs were not downloaded; completed PDFs were retained:\n' + '\n'.join(errors))
    return downloaded


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', default='data/paper_metadata.json')
    parser.add_argument('--output-dir', default='data/pdfs')
    args = parser.parse_args()
    try:
        print('\n'.join(download_pdfs(args.metadata, args.output_dir)))
    except (ValidationError, OSError) as exc:
        parser.exit(2, f'Error: {exc}\n')
