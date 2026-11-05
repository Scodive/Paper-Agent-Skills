# Revision contract

## Inputs

- Manuscript: UTF-8 Markdown/text, a single TeX file, or a text-based PDF.
- Experiments: JSON `{"experiments": [...]}` or a CSV with one metric per record.
  Each record needs a stable `id` and `status`: completed, planned, not_run,
  running, or failed. Completed records need numeric `value` and `metric`.
  Supply `method`, `dataset`, `split`, `unit`, `seed`, and a `source` log/artifact
  locator where available. Status is user-reported, not independently verified.
- References: JSON `{"references": [...]}` or BibTeX. Each needs stable `id` and
  `title`. JSON can include `excerpt` with `excerpt_source` (page/section/URL).
  Bibliographic identity remains unverified; excerpts remain supplied evidence.
  BibTeX string macros/concatenation must be expanded before importing.

Absent or empty evidence is allowed and prominently reported. Never fill missing
results with guessed values. External artifact locators are recorded, not fetched
or executed. Do not interpret a log locator as a reproduced experiment.

## Response and validation

The generated JSON Schema is the authoritative response interface. All line
coordinates refer to `manuscript.txt`, including for PDF-extracted text. Read every
chunk, including appendices. Declare all reviewed chunk IDs; coverage is an agent
statement rather than independent proof of reading.

Suggestions record severity, issue, recommendation and evidence IDs. Claim
reviews quote actual original text and distinguish supported, contradicted,
needs_evidence, not_run, and citation_identity_only. A supported assessment needs
a completed experiment or source excerpt; check its actual meaning yourself.

Edits replace inclusive complete line ranges with an exact original-text match.
They cannot overlap. Use `editorial`, `evidence_correction`, `remove_unsupported`,
or `citation_fix`. Every newly introduced number must match cited completed
results (including fraction/percent conversion) or a cited source excerpt. To add
a derived statistic, first supply an explicit record with its formula and inputs.
Unresolved new citation keys, stale originals, unknown evidence IDs and planned
results used as numerical evidence are rejected.

Mechanical checks cannot establish semantic entailment, correct dataset/split,
causality, significance, originality, truth of user-supplied records, or acceptance.
The host agent must assess these and disclose uncertainty. Repeated values and
stronger wording can evade lexical checks; read `claim_evidence.json` and the diff.

## Outputs

`results/` contains revised Markdown or TeX, `suggestions.md/json`,
`claim_evidence.json`, `changes.diff`, `checks.md/json`, validated `response.json`
and output hashes. `check` verifies snapshots, revalidates the response, reproduces
the edit application and recomputes checks. Original inputs are never overwritten;
use a new output directory for another run or result version.

PDF output is a revision of extracted text, not preserved PDF layout. Inspect the
original pages, tables, equations and figures. Multi-file TeX projects must be
flattened before review. No OCR, LaTeX compile, external citation verification or
experiment execution is performed by this workflow.
