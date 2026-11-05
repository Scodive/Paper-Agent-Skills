---
name: academic-paper-writing
description: Revise academic manuscripts using supplied experiment records and bibliography, with anchored suggestions, exact edits and evidence checks. Also plan outlines and drafts with missing results explicitly marked.
metadata:
  version: "2.0.0"
  author: Paper-Agent
---

# Evidence-aware academic writing

Use real manuscript text, experiment records and bibliography as the working
materials. Preserve supported technical content and separate hypotheses, planned
experiments, user-reported results and independently verified evidence.

## Standalone installation

When this skill was installed with the skills CLI, its execution tools are bundled
under `scripts/`. Set `SKILL_DIR` to this installed skill directory. If needed,
create a Python 3.10+ virtual environment and install its dependencies:

```bash
python3 -m venv .paper-agent-venv
.paper-agent-venv/bin/python -m pip install -r "$SKILL_DIR/scripts/requirements.txt"
.paper-agent-venv/bin/python "$SKILL_DIR/scripts/paper_agent.py" --help
```

Use that Python executable and runner in place of `python3 src/main.py` below.
Keep the skill installation separate from the paper's working directory. The
runner works outside the source repository. Do not reinstall if the active Python
already provides the listed dependencies. An installed `paper-agent` CLI is also
supported. No model API key is required by the execution tools.

## Revision workflow

Read [the revision contract](references/revision.md) when preparing or responding
to a revision package. From a repository checkout:

```bash
python3 src/main.py prepare --paper paper.tex --experiments results.csv --references refs.bib --out runs/review-01
```

Read the generated `agent_task.md`, complete `manuscript.txt`, all chunks and
`materials.json`. Write `response.json` matching `response.schema.json`, then:

```bash
python3 src/main.py apply --run runs/review-01 --response runs/review-01/response.json
python3 src/main.py check --run runs/review-01
```

With an installed distribution, replace `python3 src/main.py` with `paper-agent`.
The scripts do not invoke a model; the host agent performs review and writing.

- Anchor suggestions and claim assessments to original lines and evidence IDs.
- Make focused edits; retain notation, methods and supported conclusions.
- Do not invent experiments, numeric outcomes, citations or completed revisions.
- Bibliographic metadata alone cannot establish source support. Read the source
  excerpt or mark the claim as needing evidence; a matching key is insufficient.
- Check whether evidence uses the same method, dataset, split, metric and units.
  A matching number alone cannot establish support or statistical significance.
- Treat writing patterns as contextual examples, never mandatory contribution
  counts, sentence lengths, or guarantees of publication quality.
- Conference requirements must include venue, year, track, submission stage and
  official source. Do not rely on a timeless page-limit table.

## Planning without completed evidence

`outline --idea "..." --out runs/outline-01` and `draft --outline outline.json
--out runs/draft-01` export host-agent tasks. Leave results null or visibly marked
`[NEEDS_EVIDENCE]`. These are planning artifacts, not evidence of completed work.
