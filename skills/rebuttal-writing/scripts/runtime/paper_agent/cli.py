"""Command-line entry points; importing this module never needs API credentials."""

import argparse
import shlex
import sys
from pathlib import Path

from .skills import load_skills
from .storage import ValidationError, json_text
from .tasks import export_task
from .workflow import apply_response, check_run, prepare


def parser():
    root = argparse.ArgumentParser(description="Paper-Agent: local evidence-aware revision with your host agent")
    commands = root.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare", help="Package a complete paper and evidence for the host agent")
    p.add_argument("--paper", required=True, type=Path)
    p.add_argument("--experiments", type=Path)
    p.add_argument("--references", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--skills-dir", type=Path)
    p.add_argument("--patterns", type=Path, help="Optional source-anchored learned pattern database")
    p = commands.add_parser("apply", help="Validate an agent response and create a revision and reports")
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--response", required=True, type=Path)
    p.add_argument("--out", type=Path, help="New result directory; default RUN/results")
    p = commands.add_parser("check", help="Recheck snapshots, edits and manuscript heuristics")
    p.add_argument("--run", required=True, type=Path)
    p.add_argument("--results", type=Path)
    p.add_argument("--fail-on-findings", action="store_true", help="Return exit code 1 when manuscript findings remain")
    p = commands.add_parser("validate-skills", help="Validate skill names, metadata and reference links")
    p.add_argument("--skills-dir", type=Path)
    for kind in ("outline", "draft", "rebuttal", "slides"):
        p = commands.add_parser(kind, help=f"Export a {kind} task for the host agent (no model API)")
        p.add_argument("--out", required=True, type=Path)
        if kind == "outline":
            p.add_argument("--idea", required=True)
        if kind == "draft":
            p.add_argument("--outline", required=True, type=Path)
        if kind in {"rebuttal", "slides"}:
            p.add_argument("--paper", required=True, type=Path)
        if kind == "rebuttal":
            p.add_argument("--reviews", required=True, type=Path)
    return root


def _legacy(argv):
    if "--mode" not in argv:
        return argv
    old = argparse.ArgumentParser(description="Legacy compatibility; generation now uses host-agent tasks")
    old.add_argument("--mode", choices=["outline", "draft", "refine"], required=True)
    old.add_argument("--idea")
    old.add_argument("--outline")
    old.add_argument("--draft")
    old.add_argument("--experiments")
    old.add_argument("--references")
    old.add_argument("--out")
    args = old.parse_args(argv)
    command = "prepare" if args.mode == "refine" else args.mode
    result = [command, "--out", args.out or f"output/{args.mode}-task"]
    for key in ("idea", "outline", "experiments", "references"):
        value = getattr(args, key)
        if value is not None:
            result += [f"--{key}", value]
    if args.draft:
        result += ["--paper", args.draft]
    print("Legacy mode: exporting a host-agent task; no automatic API generation.", file=sys.stderr)
    return result


def main(argv=None):
    args = parser().parse_args(_legacy(list(sys.argv[1:] if argv is None else argv)))
    try:
        if args.command == "prepare":
            executable = Path(sys.argv[0]).resolve()
            if executable.name == "__main__.py":
                command = shlex.join([sys.executable, "-m", "paper_agent"])
            else:
                command = shlex.join([sys.executable, str(executable)])
            result = prepare(args.paper, args.out, args.experiments, args.references,
                             args.skills_dir, args.patterns, runner_command=command)
        elif args.command == "apply":
            result = apply_response(args.run, args.response, args.out)
        elif args.command == "check":
            result = check_run(args.run, args.results)
        elif args.command == "validate-skills":
            result = {"skills": [s["name"] for s in load_skills(args.skills_dir)], "state": "valid"}
        else:
            result = export_task(args.command, args.out, paper=getattr(args, "paper", None),
                                 reviews=getattr(args, "reviews", None), idea=getattr(args, "idea", None),
                                 outline=getattr(args, "outline", None))
        print(json_text(result), end="")
        if args.command == "check" and args.fail_on_findings:
            check = result.get("revised", result["original"])
            pending = result.get("agent_review", {}).get("pending_suggestions", [])
            return 1 if check["findings"] or pending or result["state"] == "prepared_awaiting_agent_review" else 0
        return 0
    except (ValidationError, OSError, UnicodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
