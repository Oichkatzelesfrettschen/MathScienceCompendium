#!/usr/bin/env python3
"""Render the canonical hypothesis registry as an auditable Markdown report."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "data" / "registry" / "hypothesis_registry.json"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "framework" / "HYPOTHESIS_REGISTRY.md"


def load_registry(path: Path) -> dict[str, Any]:
    """Load the hypothesis registry and reject non-ASCII durable content."""
    raw_text = path.read_text(encoding="ascii")
    payload = json.loads(raw_text)
    if not isinstance(payload, dict):
        raise TypeError("Hypothesis registry must be a JSON object")
    return payload


def markdown_list(items: list[str]) -> list[str]:
    """Render a nonempty string sequence as Markdown bullets."""
    return [f"- {item}" for item in items]


def render_report(payload: dict[str, Any]) -> str:
    """Create a deterministic report from registry content."""
    hypotheses = payload["hypotheses"]
    program_counts = Counter(item["program_id"] for item in hypotheses)
    research_counts = Counter(item["research_status"] for item in hypotheses)
    archival_groups = payload["archival_conjecture_dispositions"]
    archival_count = sum(len(group["items"]) for group in archival_groups)
    lines = [
        "# Hypothesis Registry",
        "",
        "This is the human-readable view of `data/registry/hypothesis_registry.json`.",
        "The JSON registry is canonical. Contract consistency is not scientific admission.",
        "A supported or negative result remains out of the paper until its locked decision",
        "rule is evaluated and a cache-isolated clean-environment rerun is retained.",
        "",
        "## Coverage",
        "",
        f"- Registered hypotheses: {len(hypotheses)}",
        f"- Canonical source claims covered: {sum(len(item['source_claim_ids']) for item in hypotheses)}",
        f"- Active: {research_counts['active']}",
        f"- Blocked: {research_counts['blocked']}",
        f"- Excluded: {research_counts['excluded']}",
        f"- Falsified: {research_counts['falsified']}",
        f"- Not supported: {research_counts['not_supported']}",
        f"- Explicit archival conjectures and predictions dispositioned: {archival_count}",
        "- Programs: "
        + ", ".join(f"{key}={program_counts[key]}" for key in sorted(program_counts)),
        "",
        "## Promotion policy",
        "",
    ]
    policy = payload["promotion_policy"]
    lines.extend(
        markdown_list(
            [
                policy["paper_admission_rule"],
                policy["independent_reproduction_rule"],
                policy["literature_rule"],
            ]
        )
    )

    for hypothesis in hypotheses:
        lines.extend(
            [
                "",
                f"## {hypothesis['id']}: {hypothesis['title']}",
                "",
                f"- Program: `{hypothesis['program_id']}`",
                f"- Source claims: {', '.join(f'`{item}`' for item in hypothesis['source_claim_ids'])}",
                f"- Research status: `{hypothesis['research_status']}`",
                f"- Implementation status: `{hypothesis['implementation_status']}`",
                f"- Independent reproduction: `{hypothesis['independent_reproduction']['status']}`",
                f"- Paper promotion: `{hypothesis['paper_promotion']}`",
                "",
                "Formal statement:",
                "",
                hypothesis["formal_statement"],
                "",
                "Observable predictions:",
                "",
            ]
        )
        for prediction in hypothesis["observable_predictions"]:
            lines.append(
                f"- `{prediction['id']}`: {prediction['observable']} "
                f"Prediction: {prediction['expected_relation']} "
                f"Method: {prediction['measurement_method']}"
            )
        lines.extend(["", "Controls:", ""])
        lines.extend(markdown_list(hypothesis["controls"]))
        lines.extend(["", "Falsification thresholds:", ""])
        lines.extend(markdown_list(hypothesis["falsification_thresholds"]))
        lines.extend(["", "Required evidence:", ""])
        for evidence in hypothesis["required_evidence"]:
            paths = ", ".join(f"`{path}`" for path in evidence["artifact_paths"])
            suffix = f" Artifacts: {paths}." if paths else ""
            lines.append(
                f"- `{evidence['kind']}` / `{evidence['status']}`: "
                f"{evidence['description']}.{suffix}"
            )
        source_ids = hypothesis["literature_source_ids"]
        lines.extend(
            [
                "",
                "Aligned literature: "
                + (", ".join(f"`{source_id}`" for source_id in source_ids) or "none admitted"),
            ]
        )
    lines.extend(
        [
            "",
            "## Archival conjecture dispositions",
            "",
            "These dormant legacy items are not manuscript claims. Each remains traceable",
            "so it cannot silently re-enter the active authority surface.",
        ]
    )
    for group in archival_groups:
        lines.extend(["", f"### `{group['source_relpath']}`", ""])
        for item in group["items"]:
            mappings = ", ".join(
                f"`{hypothesis_id}`" for hypothesis_id in item["mapped_hypothesis_ids"]
            )
            mapping_suffix = f" Maps to {mappings}." if mappings else ""
            lines.append(
                f"- `{item['id']}` ({item['locator']}): {item['title']} - "
                f"`{item['disposition']}`. {item['rationale']}{mapping_suffix}"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    registry_path = arguments.registry
    output_path = arguments.output
    if not registry_path.is_absolute():
        registry_path = REPO_ROOT / registry_path
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    report = render_report(load_registry(registry_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="ascii")
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
