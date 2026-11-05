import copy
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import downloader
import scraper
import processor
import skills_analyzer
from paper_agent.storage import ValidationError, read_json, write_json, digest
from paper_agent.workflow import prepare


def note(key, venue='Example/2026', label='Accept (Poster)', replies=()):
    return SimpleNamespace(id=key, number=1,
        content={'venueid': {'value': venue}, 'venue': {'value': label},
                 'title': {'value': 'A paper'}, 'pdf': {'value': '/pdf?id=' + key}},
        details={'directReplies': list(replies)})


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_collection_filters_acceptance_and_oral_with_explicit_basis(self):
        notes = [note('poster'), note('oral', label='Example 2026 Oral'),
                 note('withdrawn', venue='Example/2026/Withdrawn', label='Oral'),
                 note('negative', label='Accept (Poster), not Oral')]
        client = SimpleNamespace(get_all_notes=lambda **kwargs: notes)
        papers = scraper.fetch_top_papers('Example/2026', category='oral', client=client)
        self.assertEqual([p['id'] for p in papers], ['oral'])
        self.assertTrue(papers[0]['classification_basis'])
        accepted = scraper.fetch_top_papers('Example/2026', category='accepted', client=client)
        self.assertEqual(len(accepted), 3)

    def test_decision_notes_support_classification_and_unknown_award_is_not_invented(self):
        reply = {'id': 'decision', 'invitations': ['Example/2026/Paper1/-/Decision'],
                 'content': {'decision': {'value': 'Accept (Spotlight)'}}}
        client = SimpleNamespace(get_all_notes=lambda **kwargs: [note('x', replies=[reply])])
        self.assertEqual(len(scraper.fetch_top_papers('Example/2026', category='spotlight', client=client)), 1)
        self.assertEqual(scraper.fetch_top_papers('Example/2026', category='best-paper', client=client), [])

    def test_downloader_rejects_html_and_does_not_publish_partial_files(self):
        metadata = self.root / 'meta.json'
        write_json(metadata, [{'id': 'id', 'title': 'A paper', 'pdf_url': 'https://example.org/paper.pdf'}])
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def raise_for_status(self): pass
            def iter_content(self, **kwargs):
                yield b'<html>Not a PDF</html>'
        target = self.root / 'pdfs'
        with patch('downloader.requests.get', return_value=Response()) as request:
            with self.assertRaisesRegex(ValidationError, 'not a PDF'):
                downloader.download_pdfs(metadata, target)
        self.assertEqual(list(target.iterdir()), [])
        self.assertEqual(request.call_args.kwargs['timeout'], (10, 60))

    def test_failed_download_can_be_retried_without_a_cached_partial_pdf(self):
        metadata = self.root / 'meta.json'
        write_json(metadata, [{'id': 'id', 'title': 'A paper', 'pdf_url': 'https://example.org/paper.pdf'}])
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def raise_for_status(self): pass
            def iter_content(self, **kwargs):
                yield b'%PDF-1.7\npartial'
                raise downloader.requests.ConnectionError('interrupted')
        target = self.root / 'pdfs'
        with patch('downloader.requests.get', return_value=Response()):
            with self.assertRaises(ValidationError):
                downloader.download_pdfs(metadata, target)
        self.assertEqual(list(target.iterdir()), [])

    def test_legacy_truncated_cache_is_preserved_and_reported(self):
        metadata = self.root / 'meta.json'
        write_json(metadata, [{'id': 'id', 'title': 'A paper', 'pdf_url': 'https://example.org/paper.pdf'}])
        target = self.root / 'pdfs'
        target.mkdir()
        cached = target / 'id_A_paper.pdf'
        cached.write_bytes(b'%PDF-incomplete cache from an older version')
        with patch('downloader.requests.get') as request:
            with self.assertRaisesRegex(ValidationError, 'Existing cache is invalid'):
                downloader.download_pdfs(metadata, target)
            request.assert_not_called()
        self.assertEqual(cached.read_bytes(), b'%PDF-incomplete cache from an older version')

    def test_pdf_processor_keeps_page_map_and_refuses_overwrite(self):
        source = self.root / 'source.pdf'
        source.write_bytes(b'unit-test placeholder; extraction is mocked')
        target = self.root / 'paper.md'
        with patch('processor.load_paper', return_value=('First\nTail\n', [{'page':1,'start_line':1,'end_line':2}], ['layout unverified'])):
            processor.pdf_to_markdown(source, target)
            with self.assertRaises(ValidationError):
                processor.pdf_to_markdown(source, target)
        record = read_json(target.with_suffix('.source.json'))
        self.assertEqual(record['text_sha256'], digest(target.read_text()))
        self.assertEqual(record['pdf_sha256'], digest(source.read_bytes()))

    def test_extraction_task_covers_tail_and_import_requires_actual_quote(self):
        paper = self.root / 'paper.md'
        text = '# Introduction\n' + 'Context line.\n' * 1000 + '# Tail\nWe compare the components separately.\n'
        paper.write_text(text)
        task = self.root / 'task'
        skills_analyzer.export_paper_task(paper, task)
        pieces = read_json(task / 'chunks.json')
        self.assertEqual(pieces[-1]['end_line'], len(text.splitlines()))
        response = {'schema_version': 1, 'source_sha256': digest(text), 'patterns': [
            {'name': 'Component comparisons', 'when_to_use': 'When a method has separable components',
             'guidance': 'Compare the components separately with controlled evidence.',
             'source_quote': 'We compare the components separately.',
             'start_line': len(text.splitlines()), 'end_line': len(text.splitlines())}]}
        path, base = self.root / 'response.json', self.root / 'base.json'
        write_json(path, response)
        self.assertEqual(skills_analyzer.import_response(task, path, base)['state'], 'imported')
        self.assertEqual(skills_analyzer.import_response(task, path, base)['state'], 'already_imported')
        before = base.read_bytes()
        response['patterns'][0]['source_quote'] = 'Invented quotation.'
        write_json(path, response)
        with self.assertRaisesRegex(ValidationError, 'source_quote'):
            skills_analyzer.import_response(task, path, base)
        self.assertEqual(base.read_bytes(), before)
        run = self.root / 'review'
        prepare(paper, run, patterns=base)
        materials = read_json(run / 'materials.json')
        self.assertEqual(materials['learned_patterns'][0]['patterns'][0]['name'], 'Component comparisons')
        self.assertTrue((run / 'sources/learned_patterns.json').is_file())

    def test_changed_extracted_text_is_not_assigned_stale_provenance(self):
        paper = self.root / 'paper.md'
        paper.write_text('Changed text.')
        write_json(paper.with_suffix('.source.json'), {'text_sha256': digest('Old text.')})
        with self.assertRaisesRegex(ValidationError, 'differs from provenance'):
            skills_analyzer.export_paper_task(paper, self.root / 'task')


if __name__ == '__main__':
    unittest.main()
