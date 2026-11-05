"""Load complete manuscripts and explicitly scoped, user-supplied evidence."""

import csv
import math
import re
from pathlib import Path

from .storage import ValidationError, read_json

STATUSES = {"completed", "planned", "not_run", "running", "failed"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]*$")


def load_paper(path):
    path = Path(path)
    warnings = []
    suffix = path.suffix.lower()
    pages = []
    if suffix == ".pdf":
        import fitz
        parts = []
        cursor = 1
        with fitz.open(path) as doc:
            for number, page in enumerate(doc, 1):
                # Geometric line sorting can interleave the two columns of a paper.
                # Retain the PDF's native text sequence; layout remains unverified.
                text = page.get_text(sort=False).strip()
                if not text:
                    raise ValidationError(f"PDF page {number} has no extractable text; supply OCR text.")
                part = f"<!-- Page {number} -->\n{text}\n"
                count = len(part.splitlines())
                pages.append({"page": number, "start_line": cursor, "end_line": cursor + count - 1})
                parts.append(part)
                cursor += count
        text = "".join(parts)
        warnings.append("PDF text extraction is not layout, equation, table, or figure verification. "
                        "The revision is Markdown, not an edited PDF; inspect the source pages.")
    elif suffix in {".md", ".markdown", ".txt", ".tex"}:
        text = path.read_text(encoding="utf-8")
        if suffix == ".tex" and re.search(r"\\(?:input|include)\s*\{", text):
            warnings.append("Only this TeX file is loaded; flatten input/include files before review.")
    else:
        raise ValidationError("Paper must be .md, .txt, .tex, or a text-based .pdf")
    if not text.strip():
        raise ValidationError("The manuscript is empty")
    return text, pages, warnings


def chunks(text, pages=(), target_chars=12000):
    """Whole-line chunks cover every line, including appendices. Never truncate."""
    result = []
    lines = text.splitlines()
    start = 1
    size = 0
    for number, line in enumerate(lines, 1):
        if size and size + len(line) + 1 > target_chars:
            result.append(_chunk(lines, start, number - 1, pages, len(result)))
            start, size = number, 0
        size += len(line) + 1
    if lines:
        result.append(_chunk(lines, start, len(lines), pages, len(result)))
    return result


def _chunk(lines, start, end, pages, index):
    return {"id": f"paper:{index + 1:04}", "start_line": start, "end_line": end,
            "pages": [p["page"] for p in pages if p["end_line"] >= start and p["start_line"] <= end],
            "text": "\n".join(lines[start - 1:end])}


def _entries(path, key):
    data = read_json(path)
    if isinstance(data, dict):
        data = data.get(key)
    if not isinstance(data, list) or any(not isinstance(x, dict) for x in data):
        raise ValidationError(f"{path}: expected a list, or an object containing '{key}' list")
    return data


def _unique(entries, kind):
    ids = set()
    for entry in entries:
        key = entry.get("id")
        if not isinstance(key, str) or not ID.fullmatch(key) or key in ids:
            raise ValidationError(f"{kind}: missing, duplicate or invalid id: {key!r}")
        ids.add(key)


def load_experiments(path):
    if path is None:
        return [], ["No experiment records supplied. Experimental claims remain unverified."]
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            entries = list(csv.DictReader(f))
    elif path.suffix.lower() == ".json":
        entries = _entries(path, "experiments")
    else:
        raise ValidationError("Experiments must be JSON or CSV")
    _unique(entries, "experiments")
    warnings = []
    for index, entry in enumerate(entries):
        status = entry.get("status")
        if status not in STATUSES:
            raise ValidationError(f"Experiment {entry['id']}: status must be one of {sorted(STATUSES)}")
        value = entry.get("value")
        if value not in (None, ""):
            try:
                if isinstance(value, bool):
                    raise ValueError()
                value = float(value)
                if not math.isfinite(value):
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(f"Experiment {entry['id']}: value must be a finite number") from None
            entry["value"] = value
        if status == "completed" and (value in (None, "") or not entry.get("metric")):
            raise ValidationError(f"Completed experiment {entry['id']} needs metric and numeric value")
        for field in ("source", "metric", "unit", "dataset", "split", "method"):
            if field in entry and not isinstance(entry[field], str):
                raise ValidationError(f"Experiment {entry['id']}: {field} must be text")
        entry["evidence_id"] = f"exp:{entry['id']}"
        entry["locator"] = f"record {index + 1} in supplied experiments file"
        entry["provenance_status"] = "user_supplied_not_reproduced"
        if not entry.get("source"):
            warnings.append(f"{entry['evidence_id']}: no log/artifact locator supplied.")
    if not entries:
        warnings.append("Experiment list is empty. No experiment is established as completed.")
    return entries, warnings


def parse_bibtex(text):
    """Balanced BibTeX entries; reject macros/concatenation instead of guessing."""
    entries = []
    pos = 0
    while match := re.search(r"@([A-Za-z]+)\s*([({])", text[pos:]):
        kind = match[1].lower()
        begin = pos + match.end()
        opening = match[2]
        closing = "}" if opening == "{" else ")"
        depth, quoted, escaped, end = 1, False, False, begin
        for end in range(begin, len(text)):
            c = text[end]
            if escaped:
                escaped = False
                continue
            if c == "\\":
                escaped = True
                continue
            if c == '"' and depth == 1:
                quoted = not quoted
            if not quoted:
                if c == opening:
                    depth += 1
                elif c == closing:
                    depth -= 1
                    if depth == 0:
                        break
        if depth:
            raise ValidationError("Unbalanced BibTeX entry")
        body = text[begin:end]
        pos = end + 1
        if kind in {"comment", "preamble"}:
            continue
        if kind == "string":
            raise ValidationError("Expand BibTeX @string macros before importing")
        key, separator, fields = body.partition(",")
        if not separator:
            raise ValidationError("BibTeX entry needs a citation key and fields")
        entry = {"id": key.strip(), "entry_type": kind}
        while fields.strip(" \t\r\n,"):
            field = re.match(r"\s*,?\s*([A-Za-z_]+)\s*=\s*", fields)
            if not field:
                raise ValidationError(f"Unsupported BibTeX field in {key}")
            name = field[1].lower()
            fields = fields[field.end():]
            if not fields:
                raise ValidationError(f"Missing BibTeX field value in {key}")
            if fields[0] in '{"':
                opener = fields[0]
                closer = "}" if opener == "{" else '"'
                nesting, escaped = 1, False
                for end in range(1, len(fields)):
                    c = fields[end]
                    if escaped:
                        escaped = False
                        continue
                    if c == "\\":
                        escaped = True
                        continue
                    if opener == "{" and c == "{":
                        nesting += 1
                    if c == closer:
                        nesting -= 1
                        if nesting == 0:
                            break
                if nesting:
                    raise ValidationError(f"Unbalanced BibTeX field in {key}")
                value, fields = fields[1:end], fields[end + 1:]
            else:
                raw = re.match(r"\d+", fields)
                if not raw:
                    raise ValidationError(f"Expand BibTeX string macros in {key}")
                value, fields = raw[0], fields[raw.end():]
            entry[name] = value
            if fields.strip() and not fields.lstrip().startswith(","):
                raise ValidationError(f"Unsupported BibTeX concatenation or missing comma in {key}")
        entries.append(entry)
    if not entries:
        raise ValidationError("No bibliography entries found")
    return entries


def load_references(path):
    if path is None:
        return [], ["No bibliography supplied. Citation identities remain unverified."]
    path = Path(path)
    if path.suffix.lower() == ".bib":
        entries = parse_bibtex(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".json":
        entries = _entries(path, "references")
    else:
        raise ValidationError("References must be .bib or JSON")
    _unique(entries, "references")
    for index, entry in enumerate(entries):
        if not isinstance(entry.get("title"), str) or not entry["title"].strip():
            raise ValidationError(f"Reference {entry['id']} needs a title")
        if "excerpt" in entry and (not isinstance(entry["excerpt"], str) or not entry["excerpt"].strip()
                                  or not isinstance(entry.get("excerpt_source"), str)
                                  or not entry["excerpt_source"].strip()):
            raise ValidationError(f"Reference {entry['id']}: excerpt needs text and excerpt_source")
        entry["evidence_id"] = f"ref:{entry['id']}"
        entry["locator"] = f"bibliography entry {index + 1}"
        entry["identity_status"] = "user_supplied_unverified"
        entry["support_status"] = "supplied_excerpt_unverified" if entry.get("excerpt") else "metadata_only"
    return entries, ["Bibliographic metadata is user-supplied, not independently verified. "
                     "A matching citation key does not establish that a source supports a claim."]


def citations(text):
    """Common TeX and Pandoc citations; numeric brackets are treated as candidates."""
    text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1[^\n]*", "", text)
    found = set()
    for match in re.finditer(r"\\(?:cite[A-Za-z]*)(?:\*?)(?:\s*\[[^\]]*\])*\s*\{([^}]+)\}", text):
        found.update(x.strip() for x in match[1].split(",") if x.strip())
    found.update(key.rstrip(".:") for key in re.findall(
        r"(?<![\w@])@([A-Za-z0-9][A-Za-z0-9_.:/-]*)", text))
    for match in re.finditer(r"\[(\d+(?:\s*,\s*\d+)*)\]", text):
        keys = [x.strip() for x in match[1].split(",")]
        # Closed probability intervals in equations are not citation lists.
        if len(keys) > 1 and ("0" in keys or re.search(r"(?:∈|interval|=)\s*$", text[:match.start()])):
            continue
        found.update(keys)
    return found
