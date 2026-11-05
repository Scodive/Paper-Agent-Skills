# Validation methodology

The README reports engineering evidence and one live host-agent exercise. These
measure different things and must not be combined into a paper-quality score.

## Reproduce the engineering checks

From a source checkout with the dependencies installed:

```bash
python3 scripts/build_skill_bundles.py --check
python3 scripts/validate_release.py --out output/validation.json
```

The validator runs the complete unittest suite, attempts nine invalid response
variants, and applies the checked-in synthetic review payload. The output records
the Python version, source fingerprint, scenario outcomes, preserved-input check,
remaining findings and unresolved suggestions. The fixed response is a replay;
it does not measure the quality of a newly generated model answer.

The three distribution tests copy installed bundles into a temporary directory,
remove the source checkout from the subprocess import path, invoke each CLI,
and complete a prepare/apply/check cycle using only one copied bundle. Generated
bundles must match the canonical files under `src/paper_agent/`.

## Live DSH exercise

The recorded exercise used the installed macOS DSH runtime, version 0.2.2-rc.1,
with the existing `deepseek-account` route and `deepseek-flash` model. The three
skills were installed with skills CLI 1.7.6 into an isolated `.agents/skills/`
directory. No global skill installation or original DSH profile was modified.

A separate DSH home and a per-run overlay selected only that installed skill
root. The agent was asked to load all three skills using DSH's actual `skill`
tool, then execute academic paper revision on `examples/revision/paper.md`,
`results.csv`, and `references.bib`. It had no supplied response and was instructed
not to read the repository's pre-authored review. Subagent and plugin-management
tools were disabled. The task had a five-minute process deadline.

Completion required process exit 0, a final DSH event with reason `completed`,
and an independent invocation of this project's artifact checks. The public
receipt verifies that all 49 tested distribution files match the current bundle,
records successful canonical skill loads from the event stream, and checks the
synthetic input hashes. Raw account credentials and session logs are kept out of
the repository. The public response is included for inspection.

To create another receipt after an equivalent local DSH exercise:

```bash
python3 scripts/record_dsh_validation.py \
  --run output/dsh-validation \
  --installed-skills output/skills-install-validation/.agents/skills \
  --out output/dsh-receipt.json
```

This command inspects an existing completed run; it does not launch a model.

## Interpretation and limits

The synthetic case deliberately contains an incorrect accuracy, a mismatched
evaluation split, an unrun ablation presented as a finding, exaggerated scope,
and a missing citation. The live DSH response made six edits, removed the five
mechanical findings, and retained three evidence/source tasks. Removing warnings
is not proof that every revised claim is true. The agent's semantic judgments and
coverage declaration still need author review.

This is one case and one live model run. There is no unassisted-model baseline,
blinded writing assessment, statistical significance test, acceptance study, or
independent experiment reproduction. Rebuttal and slides have discovery/loading
coverage and task-export tests, but no live end-to-end behavioral score.

`validation/engineering.json` is a local observation. The CI workflow publishes its
own machine-readable results as artifacts; a configured workflow is not evidence
that a remote CI run has passed.


## Distribution checks

The public GitHub source at `20e8aea58402fb8fe37464b78b29344b82b49489`
was installed through skills CLI 1.7.6. All three skills installed, and all 49
published bundle files matched the installation used by the live DSH exercise.
The public skills.sh repository page returned all three skills; the CLI query
`skills find paper --owner Scodive` also returned all three. The corresponding
GitHub Actions run passed both Python 3.10 and Python 3.13 jobs. These observations
are recorded separately in [distribution.json](../validation/distribution.json).

The platform also displayed a historical Snyk **medium** warning for the rebuttal
skill, dated September 18, 2026, about ingesting third-party reviewer content.
That scan predates the published source commit. It is not counted as a passing
security audit or represented as a fresh scan of this release. Review texts are
treated as data by the task exporter; all external source content still requires
careful interpretation by the host agent. See the [platform report](https://skills.sh/scodive/paper-agent-skills/rebuttal-writing/security/snyk).
