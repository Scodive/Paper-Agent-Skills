import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from paper_agent.checks import check_manuscript, numeric_match
from paper_agent.cli import main
from paper_agent.materials import chunks, load_experiments, load_paper, load_references, parse_bibtex
from paper_agent.skills import load_skills
from paper_agent.storage import ValidationError, read_json, write_json
from paper_agent.tasks import export_task
from paper_agent.workflow import apply_response, check_run, prepare, validate_response

FIXTURE = ROOT / 'examples/revision'


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'review'
        prepare(FIXTURE / 'paper.md', self.run, FIXTURE / 'results.csv', FIXTURE / 'references.bib')
        self.materials = read_json(self.run / 'materials.json')
        self.text = (self.run / 'manuscript.txt').read_text()
        self.response = read_json(FIXTURE / 'response_fixture.json')
        self.response['bundle_id'] = self.materials['bundle_id']

    def apply(self, response=None):
        path = self.root / 'response.json'
        write_json(path, response or self.response)
        return apply_response(self.run, path)

    def test_end_to_end_preserves_source_and_reports_pending_work(self):
        before = (FIXTURE / 'paper.md').read_bytes()
        result = self.apply()
        self.assertEqual(result['edits'], 5)
        revised = (self.run / 'results/revised.md').read_text()
        self.assertIn('93% accuracy', revised)
        self.assertNotIn('98%', revised)
        self.assertIn('has not been run', revised)
        self.assertNotIn('missing2026', revised)
        self.assertEqual((FIXTURE / 'paper.md').read_bytes(), before)
        report = check_run(self.run)
        self.assertEqual(len(report['agent_review']['pending_suggestions']), 2)
        self.assertEqual(report['scientific_validation'], 'not_established')
        self.assertEqual(report['revised']['citations']['identity_verification'], 'not_performed')
        self.assertTrue((self.run / 'results/changes.diff').read_text())

    def test_rejects_fabricated_number_even_when_marked_editorial(self):
        self.response['edits'][0]['replacement'] = 'Our method achieves 99% accuracy.'
        self.response['edits'][0]['kind'] = 'editorial'
        with self.assertRaisesRegex(ValidationError, 'new number'):
            self.apply()
        self.assertFalse((self.run / 'results').exists())

    def test_rejects_planned_result_as_evidence(self):
        edit = self.response['edits'][0]
        edit['evidence_ids'] = ['exp:robustness']
        with self.assertRaisesRegex(ValidationError, 'completed results'):
            self.apply()

    def test_rejects_new_unknown_citation(self):
        self.response['edits'][0]['replacement'] = 'See [@invented].'
        with self.assertRaisesRegex(ValidationError, 'new unresolved citations'):
            self.apply()

    def test_rejects_unknown_evidence_stale_text_overlap_wrong_bundle_and_coverage(self):
        changes = [
            lambda r: r['edits'][0].update(evidence_ids=['exp:fake']),
            lambda r: r['edits'][0].update(original='stale text'),
            lambda r: r['edits'].append(copy.deepcopy(r['edits'][0]) | {'id': 'overlap'}),
            lambda r: r.update(bundle_id='different'),
            lambda r: r.update(reviewed_chunks=[]),
        ]
        for change in changes:
            with self.subTest(change=change):
                response = copy.deepcopy(self.response)
                change(response)
                with self.assertRaises(ValidationError):
                    validate_response(response, self.materials, self.text)

    def test_citation_metadata_cannot_support_a_scientific_claim(self):
        claim = self.response['claim_reviews'][2]
        claim['status'] = 'supported'
        with self.assertRaisesRegex(ValidationError, 'completed result or source excerpt'):
            self.apply()

    def test_checks_reject_modified_input_snapshot(self):
        (self.run / 'sources/experiments.csv').write_text('changed')
        with self.assertRaisesRegex(ValidationError, 'Snapshot changed'):
            self.apply()

    def test_checks_reject_modified_output(self):
        self.apply()
        (self.run / 'results/revised.md').write_text('changed')
        with self.assertRaisesRegex(ValidationError, 'Snapshot changed'):
            check_run(self.run)

    def test_existing_run_and_results_are_not_overwritten(self):
        with self.assertRaises(ValidationError):
            prepare(FIXTURE / 'paper.md', self.run)
        self.apply()
        with self.assertRaises(ValidationError):
            self.apply()

    def test_no_truncation_and_full_coverage_required(self):
        paper = self.root / 'long.md'
        text = '# Main\n' + ('Some contextual manuscript material.\n' * 1000) + '# Appendix\nTail result achieves 77% accuracy.\n'
        paper.write_text(text)
        run = self.root / 'long-run'
        prepare(paper, run)
        materials = read_json(run / 'materials.json')
        pieces = materials['paper']['chunks']
        self.assertGreater(len(pieces), 1)
        self.assertEqual('\n'.join(c['text'] for c in pieces) + '\n', text)
        self.assertEqual(pieces[-1]['end_line'], len(text.splitlines()))
        baseline = check_run(run)
        self.assertTrue(any(f['line'] == len(text.splitlines()) for f in baseline['original']['findings']))
        response = copy.deepcopy(self.response)
        response.update(bundle_id=materials['bundle_id'], reviewed_chunks=[pieces[0]['id']], edits=[], suggestions=[], claim_reviews=[])
        with self.assertRaisesRegex(ValidationError, 'every manuscript chunk'):
            validate_response(response, materials, text)

    def test_empty_evidence_is_explicitly_unverified(self):
        run = self.root / 'no-evidence'
        prepare(FIXTURE / 'paper.md', run)
        report = check_run(run)
        self.assertIn('No experiment records', ' '.join(report['warnings']))
        self.assertEqual(report['state'], 'prepared_awaiting_agent_review')
        self.assertEqual(report['original']['experiment_status_counts'], {})

    def test_failed_validation_leaves_no_partial_result(self):
        self.response['edits'][0]['start_line'] = 10000
        with self.assertRaises(ValidationError):
            self.apply()
        self.assertFalse((self.run / 'results').exists())

    def test_extra_fields_and_boolean_line_numbers_rejected(self):
        for alter in (lambda r: r.update(passed=True), lambda r: r['edits'][0].update(start_line=True)):
            response = copy.deepcopy(self.response)
            alter(response)
            with self.assertRaises(ValidationError):
                validate_response(response, self.materials, self.text)

    def test_cli_exit_codes_distinguish_validation_and_manuscript_findings(self):
        import contextlib, io
        self.apply()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['check', '--run', str(self.run), '--fail-on-findings']), 1)
            self.assertEqual(main(['check', '--run', str(self.root / 'absent')]), 2)
            self.assertEqual(main(['check', '--run', str(self.run)]), 0)

    def test_unreviewed_clean_paper_and_missing_explicit_result_are_not_passed(self):
        import contextlib, io
        paper = self.root / 'clean.md'
        paper.write_text('A plain manuscript without quantitative claims.\n')
        run = self.root / 'clean'
        prepare(paper, run)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['check', '--run', str(run), '--fail-on-findings']), 1)
        with self.assertRaisesRegex(ValidationError, 'Results directory does not exist'):
            check_run(run, self.root / 'missing-results')

    def test_tex_revision_retains_tex_output(self):
        paper = self.root / 'paper.tex'
        paper.write_text('\\section{Method}\nA statement.\n')
        run = self.root / 'tex-run'
        prepare(paper, run)
        materials = read_json(run / 'materials.json')
        response = {'schema_version': 1, 'bundle_id': materials['bundle_id'], 'summary': 'No edits required.',
                    'reviewed_chunks': [c['id'] for c in materials['paper']['chunks']],
                    'suggestions': [], 'edits': [], 'claim_reviews': []}
        path = self.root / 'tex-response.json'
        write_json(path, response)
        apply_response(run, path)
        self.assertEqual((run / 'results/revised.tex').read_text(), paper.read_text())

    def test_no_edit_preserves_manuscript_bytes_after_utf8_read(self):
        for text in ('No final newline', 'Two\n\n', 'Line\n'):
            from paper_agent.workflow import revise
            self.assertEqual(revise(text, []), text)


class MaterialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_fraction_percent_conversion_respects_units(self):
        result = {'status': 'completed', 'value': 0.93, 'unit': 'fraction'}
        self.assertTrue(numeric_match('93%', result))
        self.assertTrue(numeric_match('0.93', result))
        self.assertFalse(numeric_match('93', result))
        self.assertFalse(numeric_match('93%', result | {'status': 'planned'}))

    def test_tex_percent_citation_identifiers_and_heading_ordinals(self):
        from paper_agent.checks import numbers
        self.assertEqual(numbers(r'Accuracy is 93\% [1] and [@key2024].'), ['93%'])
        self.assertEqual(numbers(r'\\cite{ref2024} reports 0.93.'), ['0.93'])
        self.assertEqual(numbers('## 2.1 Experimental results\nAccuracy is 93%.'), ['93%'])

    def test_real_pdf_false_positive_patterns_and_standalone_table_cells(self):
        from paper_agent.materials import citations
        self.assertEqual(citations('p ∈ [0, 1]'), set())
        self.assertEqual(citations('Prior work [1, 2].'), {'1', '2'})
        self.assertEqual(citations('Prior work @guo2017.'), {'guo2017'})
        results, _ = load_experiments(FIXTURE / 'results.csv')
        text = '5. Results\nAccuracy improves (Author, 2017).\nCIFAR-100 accuracy improves.\n93%\n98%\n'
        report = check_manuscript(text, results, [])
        self.assertEqual([n['value'] for n in report['numeric_claim_candidates']], ['93%', '98%'])
        self.assertEqual([f['line'] for f in report['findings']], [5])

    def test_rejects_nonfinite_duplicate_missing_status_and_missing_completed_value(self):
        invalid = [
            [{'id': 'x', 'status': 'completed', 'metric': 'accuracy', 'value': 'NaN'}],
            [{'id': 'x', 'status': 'planned'}, {'id': 'x', 'status': 'not_run'}],
            [{'id': 'x', 'metric': 'accuracy', 'value': 1}],
            [{'id': 'x', 'status': 'completed', 'metric': 'accuracy'}],
        ]
        path = self.root / 'results.json'
        for entries in invalid:
            write_json(path, entries)
            with self.assertRaises(ValidationError):
                load_experiments(path)

    def test_completed_zero_is_valid(self):
        path = self.root / 'results.json'
        write_json(path, [{'id': 'zero', 'status': 'completed', 'metric': 'error', 'value': 0}])
        entries, warnings = load_experiments(path)
        self.assertEqual(entries[0]['value'], 0)
        self.assertIn('not_reproduced', entries[0]['provenance_status'])

    def test_balanced_bibtex_nested_braces_quotes_and_numeric_year(self):
        entries = parse_bibtex('@article{key, title={A {Nested} Title}, author="Some Author", year=2024, doi={10.1/a}}')
        self.assertEqual(entries[0]['title'], 'A {Nested} Title')
        self.assertEqual(entries[0]['year'], '2024')
        for text in ('@article{k,title=unknown}', '@string{a="title"}', '@article{k,title={broken}',
                     '@article{k,title={a} # {b}}'):
            with self.assertRaises(ValidationError):
                parse_bibtex(text)

    def test_bibliography_is_never_automatically_verified(self):
        entries, _ = load_references(FIXTURE / 'references.bib')
        self.assertEqual(entries[0]['identity_status'], 'user_supplied_unverified')
        self.assertEqual(entries[0]['support_status'], 'metadata_only')
        path = self.root / 'refs.json'
        write_json(path, [{'id': 'key', 'title': 'A title', 'excerpt': 'A claim.'}])
        with self.assertRaises(ValidationError):
            load_references(path)

    def test_chunking_never_drops_a_single_very_long_line(self):
        text = 'a' * 20000 + '\ntail\n'
        pieces = chunks(text, target_chars=100)
        self.assertEqual('\n'.join(c['text'] for c in pieces) + '\n', text)

    def test_pdf_pages_have_line_map_and_empty_page_is_not_silently_skipped(self):
        class Page:
            def __init__(self, text): self.text = text
            def get_text(self, **kwargs): return self.text
        class Document(list):
            def __enter__(self): return self
            def __exit__(self, *args): pass
        with patch('fitz.open', return_value=Document([Page('First\npage'), Page('Tail 77%')])):
            text, pages, warnings = load_paper(self.root / 'paper.pdf')
        self.assertIn('Tail 77%', text)
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[-1]['end_line'], len(text.splitlines()))
        self.assertTrue(warnings)
        with patch('fitz.open', return_value=Document([Page('text'), Page('')])):
            with self.assertRaisesRegex(ValidationError, 'page 2'):
                load_paper(self.root / 'paper.pdf')

    def test_unmatched_values_do_not_become_supported_claims(self):
        results, _ = load_experiments(FIXTURE / 'results.csv')
        refs, _ = load_references(FIXTURE / 'references.bib')
        checks = check_manuscript('Accuracy is 93% on an unrelated dataset. [@guo2017]', results, refs)
        self.assertEqual(checks['numeric_claim_candidates'][0]['status'], 'value_match_only')
        self.assertEqual(checks['citations']['claim_support_verification'], 'requires_source_reading')

    def test_skills_are_loaded_and_invalid_reference_is_rejected(self):
        self.assertEqual(len(load_skills()), 3)
        skill = self.root / 'valid-name'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('---\nname: valid-name\ndescription: Example task\n---\n[Missing](references/missing.md)\n')
        with self.assertRaisesRegex(ValidationError, 'Missing or nonlocal'):
            load_skills(self.root)

    def test_outline_rebuttal_and_slides_are_explicit_agent_tasks(self):
        export_task('outline', self.root / 'outline', idea='A new hypothesis')
        for kind in ('rebuttal', 'slides'):
            out = self.root / kind
            export_task(kind, out, paper=FIXTURE / 'paper.md',
                        reviews=FIXTURE / 'reviews.txt' if kind == 'rebuttal' else None)
            self.assertEqual(read_json(out / 'manifest.json')['state'], 'awaiting_host_agent')
            self.assertIn('task export', (out / 'agent_task.md').read_text())


if __name__ == '__main__':
    unittest.main()
