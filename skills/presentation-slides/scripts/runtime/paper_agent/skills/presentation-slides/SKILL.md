---
name: presentation-slides
description: Turn a supplied research paper into a source-linked slide storyboard and speaker notes for a lab meeting or conference presentation.
metadata:
  version: "2.0.0"
---

# Research presentation storyboard

For a standalone skill installation, use
`python3 <installed-skill-directory>/scripts/paper_agent.py` instead of
`python3 src/main.py`. Its readable runtime is bundled in `scripts/runtime/`.
If dependencies are missing, create a Python 3.10+ virtual environment and install
`scripts/requirements.txt` from this skill. No model key is needed by the tools.

```bash
python3 src/main.py slides --paper paper.pdf --out runs/slides-01
```

Use `paper-agent` instead of `python3 src/main.py` after installation. The command
exports complete manuscript text and this skill for the host agent. Write
`storyboard.md` with slide titles, messages, source locators and speaker notes.
This workflow produces a storyboard, not a rendered PowerPoint file.

- Derive the narrative from the actual problem, insight, method, evidence and
  limitations. Do not infer acceptance or oral status from the task request.
- Choose length and timing for the stated audience and presentation slot;
  when unspecified, record the timing assumption.
- For each scientific claim and chosen figure, cite a manuscript page or line.
  Identify existing figures to reuse rather than fabricating experimental visuals.
- Keep chart units, baseline names, uncertainty and dataset/split qualifiers.
- Use a clear visual focus when it helps. Avoid mandatory word counts or a fixed
  slide count when equations, comparisons or methods require another layout.
- Flag missing evidence and required figure assets before final deck production.
