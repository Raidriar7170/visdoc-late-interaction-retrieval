"""CLI entry point for the Phase 6D frozen final comparison."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.final_comparison_run import (
    build_phase_6d_default_config,
    discover_active_openspec_changes,
    load_phase_6d_config,
    run_final_comparison,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the one-time Phase 6D final comparison."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/final_comparison.json"),
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest-output", type=Path)
    parser.add_argument("--metrics-output", type=Path)
    parser.add_argument("--rankings-output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--claim-checklist-output", type=Path)
    parser.add_argument("--no-retune-pledge-output", type=Path)
    parser.add_argument("--human-brief-output", type=Path)
    parser.add_argument("--progress-ledger-output", type=Path)
    parser.add_argument("--allow-rerun", action="store_true")
    args = parser.parse_args(argv)

    config = (
        load_phase_6d_config(args.config)
        if args.config.is_file()
        else build_phase_6d_default_config()
    )
    config = config.with_output_overrides(
        manifest=args.manifest_output,
        metrics=args.metrics_output,
        rankings=args.rankings_output,
        report=args.report_output,
        claim_checklist=args.claim_checklist_output,
        no_retune_pledge=args.no_retune_pledge_output,
        human_brief=args.human_brief_output,
        progress_ledger=args.progress_ledger_output,
        allow_rerun=args.allow_rerun,
    )
    result = run_final_comparison(
        config,
        repo_root=args.repo_root,
        active_changes=discover_active_openspec_changes(args.repo_root),
    )
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
