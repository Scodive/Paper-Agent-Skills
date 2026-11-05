# Paper-Agent-Skills

Evidence-aware research writing skills for AI agents. Revise a manuscript against supplied experiment records and references, with traceable suggestions, focused edits, and validation reports.

Includes **academic paper revision**, **rebuttal preparation**, and **presentation storyboarding**. The host agent performs the review; bundled Python tools package the evidence and validate edits. The tools require no model API key.

## Installation

Python 3.10+ and Node.js are required for this installation path. Install all three skills into the shared agent directory, which DSH can discover:

```bash
npx skills add Scodive/Paper-Agent-Skills --agent universal --skill '*' --copy --yes
python3 -m venv .paper-agent-venv
.paper-agent-venv/bin/python -m pip install -r .agents/skills/academic-paper-writing/scripts/requirements.txt
```

Each skill includes its executable tools and readable runtime. A source checkout is not required after installation. Other supported agents can be selected through the skills CLI.

## Usage

Open an agent session in your working directory and provide:

> Use academic-paper-writing to revise paper.tex against results.csv and references.bib. Use .paper-agent-venv/bin/python. Complete preparation, full-text review, edit application, and checks. Save the run to runs/review-01 and retain unresolved evidence gaps.

Read the outputs in `runs/review-01/results/`:

- `suggestions.md` — recommendations and unresolved items.
- `revised.md` or `revised.tex` — the revised manuscript.
- `changes.diff` — the exact edits.
- `checks.md` — mechanical checks and evidence limitations.

Inputs: Markdown, single-file TeX, or text-based PDF; experiment records in JSON/CSV; references in BibTeX/JSON. See [input formats](docs/input-formats.md).

## Validation

Observed results on the supplied synthetic fixture; engineering checks and live agent execution are reported separately.

| Evaluation | Observed result | Scope |
| --- | --- | --- |
| Automated test suite | 40/40 passed | Ingestion, integrity, rejection rules, and standalone bundles |
| Invalid response scenarios | 9/9 rejected | Unknown evidence, unsupported numbers, stale edits, and related cases |
| Fixed-response replay | 5 → 0 mechanical findings; 2 pending items retained | Pre-authored response, not a new model run |
| Live DSH skill loading | 3/3 skills loaded | DSH 0.2.2-rc.1; skills installed by skills CLI 1.7.6 |
| Live DSH paper revision | 5 → 0 mechanical findings; 6 edits; 3 pending items retained | One independently generated synthetic-case response |

The live DSH process completed successfully and its artifacts passed an independent recheck. Rebuttal and slide skills were loaded but did not receive end-to-end behavioral evaluation. These results **do not establish writing-quality gains, scientific correctness, or acceptance-rate improvements**.

[Engineering results](validation/engineering.json) · [DSH results](validation/dsh.json) · [DSH-generated response](validation/dsh-response.json) · [Methodology](docs/validation.md)

## Development

```bash
python3 -m pip install -e '.[collection]'
python3 scripts/build_skill_bundles.py --check
python3 scripts/validate_release.py --out output/validation.json
```

For a local output preview: `python3 examples/revision/demo.py --out output/demo-01`. This replays a pre-authored synthetic review. Source workflows and additional commands are documented in the [detailed guide](docs/advanced-usage.md).

MIT License. Collected papers retain their original licenses. Experimental records are not reproduced, references are not independently verified, and PDF layout is not preserved by the tools.
