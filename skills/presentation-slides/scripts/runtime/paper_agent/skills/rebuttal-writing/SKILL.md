---
name: rebuttal-writing
description: Prepare point-by-point responses to academic reviews using the supplied manuscript and completed evidence, tracking unanswered questions and proposed experiments separately.
metadata:
  version: "2.0.0"
---

# Evidence-based rebuttal

For a standalone skill installation, use
`python3 <installed-skill-directory>/scripts/paper_agent.py` instead of
`python3 src/main.py`. Its readable runtime is bundled in `scripts/runtime/`.
If dependencies are missing, create a Python 3.10+ virtual environment and install
`scripts/requirements.txt` from this skill. No model key is needed by the tools.

Export the complete paper and review text for the host agent:

```bash
python3 src/main.py rebuttal --paper paper.md --reviews reviews.txt --out runs/rebuttal-01
```

Use `paper-agent` instead of `python3 src/main.py` after installation. Read all
inputs and write `rebuttal.md` plus `actions.json` in the exported directory.
The command prepares a task; it does not automatically generate or submit a reply.

- Split reviews into individual points. Assess misunderstanding, valid flaw,
  missing evidence, experiment request and presentation issue on their merits.
- Link factual responses to manuscript lines and actual supplied evidence.
- Track actions as proposed, not_run, completed or verified. Never describe an
  experiment as performed or a manuscript change as applied until it exists.
- When new results are supplied, use the academic revision workflow to check
  result consistency. A rebuttal example is not experimental evidence.
- Acknowledge genuine limitations and state what the evidence cannot resolve.
- Keep replies specific and professional. Do not invent reviewer score changes
  or promise that a response will reverse a decision.
- Check the current venue/year response rules before choosing length or format.
