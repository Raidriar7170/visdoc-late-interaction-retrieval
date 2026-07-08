"""CLI entry point for the Phase 6C final-comparison dry-run gate."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from visdoc_retrieve.final_comparison_gate import (
    FinalComparisonGateConfigError,
    FinalComparisonGateOutputs,
    build_phase_6c_default_config,
    run_final_comparison_gate,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Phase 6C final-comparison dry-run gate."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run-output", type=Path)
    parser.add_argument("--readiness-report-output", type=Path)
    parser.add_argument("--claim-checklist-output", type=Path)
    parser.add_argument("--human-brief-output", type=Path)
    parser.add_argument("--progress-ledger-output", type=Path)
    args = parser.parse_args(argv)

    config = build_phase_6c_default_config()
    if any(
        value is not None
        for value in (
            args.dry_run_output,
            args.readiness_report_output,
            args.claim_checklist_output,
            args.human_brief_output,
            args.progress_ledger_output,
        )
    ):
        config = config.with_overrides(
            outputs=FinalComparisonGateOutputs(
                dry_run=args.dry_run_output or config.outputs.dry_run,
                readiness_report=(
                    args.readiness_report_output or config.outputs.readiness_report
                ),
                claim_checklist=(
                    args.claim_checklist_output or config.outputs.claim_checklist
                ),
                human_brief=args.human_brief_output or config.outputs.human_brief,
                progress_ledger=(
                    args.progress_ledger_output or config.outputs.progress_ledger
                ),
            )
        )

    try:
        result = run_final_comparison_gate(config, repo_root=args.repo_root)
    except FinalComparisonGateConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
