"""Conservative mechanical checks, never a scientific acceptance decision."""

import re

from .materials import citations

NUMBER = re.compile(r"(?<![\w.])-?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?(?:\s*\\?%)?")
RESULT_WORDS = re.compile(
    r"\b(achiev\w*|accuracy|bleu|f1|auc|outperform\w*|improv\w*|latency|speedup|result\w*|score\w*)\b"
    r"|准确率|提升|超过|实验结果|达到|延迟|得分|优于", re.I)
STRONG = re.compile(r"\b(state.of.the.art|significantly|proves?|guarantees?|all datasets|always)\b"
                    r"|显著|所有数据集|证明了|保证", re.I)


def numbers(text):
    # Citation keys, numeric citation markers and heading ordinals are identifiers,
    # not newly asserted measurements. TeX escaped percent is a percent unit.
    text = re.sub(r"\\cite[A-Za-z]*\*?(?:\s*\[[^\]]*\])*\s*\{[^}]*\}", "", text)
    text = re.sub(r"(?<![\w@])@[A-Za-z0-9][A-Za-z0-9_.:/-]*", "", text)
    text = re.sub(r"\[\d+(?:\s*,\s*\d+)*\]", "", text)
    text = re.sub(r"(?m)^(\s*#{1,6}\s+)\d+(?:\.\d+)*[.)]?\s+", r"\1", text)
    return [re.sub(r"\s+", "", m[0]).replace("\\%", "%") for m in NUMBER.finditer(text)]


def allowed_values(experiment):
    if experiment.get("status") != "completed" or experiment.get("value") is None:
        return set()
    value = float(experiment["value"])
    values = {(value, False)}
    unit = experiment.get("unit", "").lower()
    if unit in {"percent", "%"}:
        values = {(value, True)}
    elif unit in {"fraction", "ratio"}:
        values |= {(value * 100, True)}
    return values


def numeric_value(token):
    return float(token.rstrip("%")), token.endswith("%")


def numeric_match(token, experiment):
    value, percent = numeric_value(token)
    return any(percent == pct and abs(value - candidate) <= max(1e-9, abs(candidate) * 1e-9)
               for candidate, pct in allowed_values(experiment))


def check_manuscript(text, experiments, references):
    known = {r["id"] for r in references}
    used = citations(text)
    findings = []
    numeric = []
    for number, line in enumerate(text.splitlines(), 1):
        for key in sorted(citations(line) - known):
            findings.append({"code": "unresolved_citation", "severity": "high", "line": number,
                             "message": f"Citation key {key!r} is absent from supplied bibliography."})
        if re.search(r"\b(?:TODO|TBD|FIXME)\b|\[NEEDS[_ ]EVIDENCE\]", line):
            findings.append({"code": "unfinished_content", "severity": "medium", "line": number,
                             "message": "Placeholder or unresolved evidence marker remains."})
        if STRONG.search(line):
            findings.append({"code": "strong_claim_requires_review", "severity": "medium", "line": number,
                             "message": "Check scope, comparisons and statistical support for strong wording."})
        context = re.sub(r"\b[A-Za-z][A-Za-z0-9]*(?:[-−–]\d+)+\b", "", line)
        context = re.sub(r"\(\d+\)", "", context)  # equation references
        context = re.sub(r"^\s*\d+(?:\.\d+)*\.\s+", "", context)  # section/list ordinals
        if ")" in context or ";" in context:
            context = re.sub(r"\b(?:18|19|20)\d{2}[a-z]?\b", "", context)
        tokens = numbers(context)
        if RESULT_WORDS.search(context) or any(t.endswith("%") for t in tokens):
            for token in tokens:
                matches = [e["evidence_id"] for e in experiments if numeric_match(token, e)]
                numeric.append({"line": number, "value": token, "candidate_evidence_ids": matches,
                                "status": "value_match_only" if matches else "no_matching_value"})
                if not matches:
                    findings.append({"code": "unmatched_result_number", "severity": "high", "line": number,
                                     "message": f"Result-like number {token} has no matching completed record. "
                                                "This is a heuristic; dataset, split, unit and meaning need review."})
    return {"findings": findings, "numeric_claim_candidates": numeric,
            "citations": {"used": sorted(used), "missing": sorted(used - known),
                          "resolved_keys": sorted(used & known),
                          "detection_scope": "TeX/Pandoc/numeric citation candidates; author-year prose is not parsed",
                          "detection_status": "candidates_detected" if used else "no_supported_syntax_detected",
                          "identity_verification": "not_performed",
                          "claim_support_verification": "requires_source_reading"},
            "experiment_status_counts": {s: sum(e["status"] == s for e in experiments)
                                         for s in sorted({e["status"] for e in experiments})},
            "limitations": ["Checks are lexical heuristics and can have false positives and false negatives.",
                            "Value equality does not establish the correct method, dataset, split or claim.",
                            "Supplied experiment records have not been reproduced; log locators are not fetched.",
                            "Bibliography keys resolve locally; publication identity and claim support are unverified."]}


def report_markdown(report):
    lines = ["# Revision check report", "", f"State: {report['state']}", "",
             "Mechanical checks do not establish scientific validity or publication readiness.", ""]
    for name in ("original", "revised"):
        if name not in report:
            continue
        check = report[name]
        lines += [f"## {name.title()}", "", f"Findings: {len(check['findings'])}", ""]
        lines.extend(f"- L{f['line']} [{f['severity']}] {f['code']}: {f['message']}" for f in check["findings"])
        lines += ["", f"Unresolved citation keys: {', '.join(check['citations']['missing']) or 'none'}",
                  f"Detection: {check['citations']['detection_status']}",
                  f"Scope: {check['citations']['detection_scope']}", ""]
    if "agent_review" in report:
        review = report["agent_review"]
        lines += ["## Agent review", "", f"Summary: {review['summary']}", "",
                  f"Chunk coverage (agent-reported): {review['reviewed_chunks']}/{review['total_chunks']}",
                  f"Applied edits: {review['edits']}", "",
                  "Claim assessments are the agent's judgments, not independent scientific verification.", ""]
        for item in review["pending_suggestions"]:
            lines += [f"- Pending {item['id']} ({item['status']}): {item['recommendation']}"]
        lines += [""]
    lines += ["## Limitations and input warnings", ""]
    lines.extend(f"- {w}" for w in report.get("warnings", []))
    lines.extend(f"- {w}" for w in report["original"]["limitations"])
    return "\n".join(lines) + "\n"
