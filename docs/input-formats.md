# Material formats and response interface

## Manuscript

Use UTF-8 `.md`, `.markdown`, `.txt`, a single `.tex`, or a `.pdf` with extractable
text on every page. All lines are included. PDF text gets page markers and a
page-to-line map. Empty/scanned pages fail with an actionable error. Line endings
are normalized for review; original input bytes remain in `sources/`.

## Experiment records

JSON accepts a list or an object with an `experiments` list:

```json
{
  "experiments": [
    {
      "id": "main_validation",
      "status": "completed",
      "method": "proposed",
      "dataset": "actual-dataset-name",
      "split": "validation",
      "metric": "accuracy",
      "value": 0.93,
      "unit": "fraction",
      "seed": 7,
      "source": "actual-run/metrics.json:accuracy"
    },
    {
      "id": "robustness",
      "status": "not_run",
      "metric": "accuracy",
      "source": "experiment-plan.md:robustness"
    }
  ]
}
```

This illustrates the schema; it does not assert an actual measurement. CSV uses
one record per row with matching column names. IDs must be unique. Status is
required: `completed`, `planned`, `not_run`, `running`, or `failed`. Completed
records require finite numeric values and metrics; zero is valid. Missing results
remain missing. Additional descriptive fields are retained for the host agent.

`unit: fraction` or `ratio` allows 0.93 to support 93%; `percent` or `%` uses 93 to
support 93%. Unspecified or other units only permit the literal numeric scale.
Other conversions and derived statistics require explicit records with formula,
input references and provenance. Supply uncertainty, seed information, method,
data partition and artifacts where available; fields do not prove reproduction.
External `source` locators are not fetched. Add the required excerpts/records as
actual inputs rather than assuming the tool has read a referenced log.

## Bibliography

BibTeX supports balanced brace/quoted values, nested braces and numeric years.
Expand `@string` macros and `#` concatenations first; unsupported constructs fail
instead of being silently truncated. JSON supports a list or a `references` list:

```json
{
  "references": [
    {
      "id": "source_key",
      "title": "Actual source title",
      "doi": "actual-doi-if-known",
      "excerpt": "An exact passage you have read in the supplied source.",
      "excerpt_source": "Actual source, page and section"
    }
  ]
}
```

Every reference needs `id` and `title`. An optional nonempty excerpt needs a text
locator. Citation-key checks support Pandoc `[@key]`, bare `@key`, common TeX
`\\cite{key}`/`\\citep{key}`/`\\citet{key}`, and numeric `[1]` with matching numeric
reference IDs. Numeric brackets are heuristic citation candidates; arbitrary
prose-style `(Author, year)` and PDF citation typography are not fully parsed.
Supplied metadata remains `user_supplied_unverified`. Excerpts remain supplied,
unverified excerpts; no network lookup or automatic identity verification occurs.

## Host-agent response

Every prepared run includes `response.schema.json`; use its exact fields.
The runtime validates that bounded schema without a model/API dependency.

- `bundle_id` binds the answer to these exact input materials and loaded skills.
- `reviewed_chunks` must contain all `paper:NNNN` IDs exactly once.
- `suggestions`: unique ID, original inclusive lines, severity, issue,
  recommendation, evidence IDs, and status (`addressed`, `needs_author`,
  `needs_source`, `needs_experiment`). Pending items appear in the final report.
- `edits`: unique ID, original inclusive lines, exact `original`, `replacement`,
  kind, rationale and evidence IDs. Replacements operate on complete lines.
- `claim_reviews`: an exact quote in the original range, status, reasoning and
  evidence IDs. These are agent assessments, not independent source verification.

Evidence IDs are `paper:NNNN`, `exp:<record-id>` and `ref:<citation-key>`.
Scientific support cannot be established solely by quoting the submitted paper
or resolving a bibliography key. Completed experiment records and supplied
excerpts are eligible evidence, subject to the agent's semantic assessment.

The checked-in `examples/revision/response_fixture.json` is the authored synthetic
review payload without `bundle_id`; `demo.py` adds the current package ID. Do not
reuse its conclusions for another paper. Real agent responses must include all
required schema fields and be based on their own inputs.
