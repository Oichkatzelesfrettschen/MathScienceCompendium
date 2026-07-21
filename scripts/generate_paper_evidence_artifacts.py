#!/usr/bin/env python3
"""Generate paper figures and tables directly from validated registries."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_ROOT = REPO_ROOT / "data" / "registry"
FIGURE_ROOT = REPO_ROOT / "figures"
GENERATED_ROOT = REPO_ROOT / "papers" / "generated"

STATUS_ORDER = [
    "established",
    "repaired",
    "corrected",
    "bounded",
    "conjectural",
    "unsupported",
    "falsified",
    "excluded",
]
STATUS_COLORS = {
    "established": "#2F6B4F",
    "repaired": "#4C956C",
    "corrected": "#3A7CA5",
    "bounded": "#6C8EAD",
    "conjectural": "#A67C52",
    "unsupported": "#B85C5C",
    "falsified": "#8C2F39",
    "excluded": "#5B6770",
}


def load_json(filename: str) -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        json.loads((REGISTRY_ROOT / filename).read_text(encoding="ascii")),
    )


def latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(character, character) for character in text)


def humanize_identifier(value: object) -> str:
    replacements = {
        "albert": "Albert",
        "cayley": "Cayley",
        "dickson": "Dickson",
        "e7": "E7",
        "e8": "E8",
        "e9": "E9",
        "e10": "E10",
        "e11": "E11",
        "fourier": "Fourier",
        "kac": "Kac",
        "lbm": "LBM",
        "moody": "Moody",
        "planck": "Planck",
        "zpe": "ZPE",
    }
    words = [replacements.get(word, word) for word in str(value).split("_")]
    if words and words[0][0].islower():
        words[0] = words[0].capitalize()
    return " ".join(words)


def configure_plots() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "figure.dpi": 150,
            "savefig.dpi": 240,
            "savefig.bbox": "tight",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save_figure(figure: plt.Figure, filename: str) -> None:
    output_path = FIGURE_ROOT / filename
    figure.savefig(output_path, metadata={"Software": "MathScienceCompendium"})
    plt.close(figure)


def generate_claim_status_figure(claims: list[dict[str, Any]]) -> None:
    counts = Counter(str(claim["status"]) for claim in claims)
    statuses = [status for status in STATUS_ORDER if counts[status] > 0]
    values = [counts[status] for status in statuses]
    figure, axis = plt.subplots(figsize=(7.2, 3.8))
    bars = axis.barh(
        statuses,
        values,
        color=[STATUS_COLORS[status] for status in statuses],
        edgecolor="white",
    )
    axis.invert_yaxis()
    axis.set_xlabel("Canonical claims")
    axis.set_title("Claim status after executable falsification gates")
    axis.set_xlim(0, max(values) + 1.2)
    axis.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    for bar, value in zip(bars, values):
        axis.text(
            value + 0.12,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            fontweight="bold",
        )
    figure.tight_layout()
    save_figure(figure, "review_claim_status.png")


def generate_framework_overlap_figure(overlap: dict[str, Any]) -> None:
    document_ids = [str(document["id"]) for document in overlap["documents"]]
    short_labels = [
        "Alpha001",
        "Alpha003",
        "MathSpell",
        "MaxExtract",
        "PaisReply",
        "Math4",
        "Math5",
        "Aether002",
    ]
    index_by_id = {document_id: index for index, document_id in enumerate(document_ids)}
    matrix = np.eye(len(document_ids), dtype=float)
    for pair in overlap["pairwise_overlap"]:
        left_index = index_by_id[str(pair["left_document_id"])]
        right_index = index_by_id[str(pair["right_document_id"])]
        value = float(pair["block_jaccard"])
        matrix[left_index, right_index] = value
        matrix[right_index, left_index] = value

    figure, axis = plt.subplots(figsize=(7.1, 6.0))
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap="Blues")
    axis.set_xticks(range(len(short_labels)), short_labels, rotation=40, ha="right")
    axis.set_yticks(range(len(short_labels)), short_labels)
    axis.set_title("Normalized framework-block overlap")
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            value = matrix[row_index, column_index]
            if row_index == column_index or value >= 0.05:
                axis.text(
                    column_index,
                    row_index,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color="white" if value >= 0.55 else "#18212B",
                    fontsize=8,
                )
    colorbar = figure.colorbar(image, ax=axis, fraction=0.045, pad=0.04)
    colorbar.set_label("Block Jaccard similarity")
    figure.tight_layout()
    save_figure(figure, "review_framework_overlap.png")


def draw_flow_box(
    axis: plt.Axes,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    title: str,
    detail: str,
    color: str,
) -> None:
    box = FancyBboxPatch(
        (center_x - width / 2, center_y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.2,
        edgecolor=color,
        facecolor="white",
    )
    axis.add_patch(box)
    axis.text(
        center_x,
        center_y + 0.055,
        title,
        ha="center",
        va="center",
        color=color,
        fontweight="bold",
        fontsize=10,
    )
    axis.text(
        center_x,
        center_y - 0.055,
        detail,
        ha="center",
        va="center",
        color="#18212B",
        fontsize=8,
    )


def generate_evidence_flow_figure(
    claim_count: int,
    source_count: int,
    gate_count: int,
    consistent_count: int,
) -> None:
    figure, axis = plt.subplots(figsize=(9.2, 3.3))
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(0.0, 1.0)
    axis.axis("off")
    centers = [0.12, 0.37, 0.63, 0.88]
    draw_flow_box(
        axis,
        centers[0],
        0.5,
        0.19,
        0.38,
        "Bounded sources",
        f"8 framework texts\n{source_count} source PDFs",
        "#17365D",
    )
    draw_flow_box(
        axis,
        centers[1],
        0.5,
        0.19,
        0.38,
        "Canonical claims",
        f"{claim_count} deduplicated claims\nsource anchors retained",
        "#3A7CA5",
    )
    draw_flow_box(
        axis,
        centers[2],
        0.5,
        0.19,
        0.38,
        "Executable gates",
        f"{gate_count} acceptance, scope,\nand rejection contracts",
        "#A67C52",
    )
    draw_flow_box(
        axis,
        centers[3],
        0.5,
        0.19,
        0.38,
        "Audited outcomes",
        f"{consistent_count}/{gate_count} contracts consistent\nscientific outcomes remain explicit",
        "#2F6B4F",
    )
    for left_center, right_center in zip(centers[:-1], centers[1:]):
        arrow = FancyArrowPatch(
            (left_center + 0.102, 0.5),
            (right_center - 0.102, 0.5),
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.4,
            color="#5B6770",
        )
        axis.add_patch(arrow)
    axis.text(
        0.5,
        0.92,
        "Evidence flow: provenance before interpretation",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        color="#17365D",
    )
    axis.text(
        0.5,
        0.08,
        "A passing gate means the observed outcome matches its preregistered contract; it does not mean every claim is accepted.",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#5B6770",
    )
    figure.tight_layout()
    save_figure(figure, "review_evidence_flow.png")


def generate_beta_ablation_figure(beta_results: dict[str, Any]) -> None:
    contrasts = beta_results["primary_contrasts"]
    figure, axes = plt.subplots(1, 2, figsize=(9.0, 3.7))
    metric_specs = (
        ("final_window_mean_zonal_fraction", "Zonal-energy fraction effect", "#3A7CA5"),
        ("persistent_jet", "Persistent-jet prevalence effect", "#8C2F39"),
    )
    for axis, (metric, title, color) in zip(axes, metric_specs, strict=True):
        selected = [record for record in contrasts if record["metric"] == metric]
        beta_values = np.asarray([record["beta"] for record in selected])
        effects = np.asarray([record["effect_estimate"] for record in selected])
        lower = np.asarray([record["familywise_ci_lower"] for record in selected])
        upper = np.asarray([record["familywise_ci_upper"] for record in selected])
        axis.errorbar(
            beta_values,
            effects,
            yerr=np.vstack((effects - lower, upper - effects)),
            fmt="o",
            color=color,
            capsize=4,
            linewidth=1.5,
        )
        axis.axhline(0.0, color="#5B6770", linewidth=1.0)
        axis.set_xlabel(r"$\beta$")
        axis.set_ylabel("Paired effect versus beta zero")
        axis.set_title(title)
        axis.grid(axis="y", color="#E5E9ED", linewidth=0.7)
    figure.suptitle("Locked 540-run beta-plane primary contrasts", fontweight="bold")
    figure.tight_layout()
    save_figure(figure, "review_beta_ablation.png")


def generate_claim_status_rows(claims: list[dict[str, Any]], gate_results: dict[str, Any]) -> None:
    results_by_id = {str(result["claim_id"]): result for result in gate_results["results"]}
    rows = []
    for claim in claims:
        claim_id = str(claim["id"])
        result = results_by_id[claim_id]
        rows.append(
            f"{latex_escape(humanize_identifier(claim_id))} & "
            f"{latex_escape(humanize_identifier(claim['domain']))} & "
            f"{latex_escape(claim['status'])} & "
            f"{latex_escape(result['actual_gate_outcome'])} \\\\"
        )
    (GENERATED_ROOT / "review_claim_status_rows.tex").write_text(
        "\n".join(rows) + "\n\\bottomrule\n", encoding="ascii"
    )


def yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def generate_cayley_property_rows(cayley_audit: dict[str, Any]) -> None:
    rows = []
    for algebra in cayley_audit["algebras"]:
        properties = algebra["properties"]
        rows.append(
            f"{latex_escape(algebra['name'])} & {algebra['dimension']} & "
            f"{yes_no(properties['is_commutative'])} & "
            f"{yes_no(properties['is_associative'])} & "
            f"{yes_no(properties['is_alternative'])} & "
            f"{yes_no(properties['is_power_associative'])} & "
            f"{yes_no(properties['is_flexible'])} & "
            f"{yes_no(properties['norm_is_multiplicative'])} & "
            f"{yes_no(properties['has_zero_divisors'])} \\\\"
        )
    (GENERATED_ROOT / "review_cayley_property_rows.tex").write_text(
        "\n".join(rows) + "\n\\bottomrule\n", encoding="ascii"
    )


def generate_admission_rows(admission: dict[str, Any]) -> None:
    rows = []
    for package in admission["packages"]:
        rows.append(
            f"{latex_escape(humanize_identifier(package['claim_id']))} & "
            f"{latex_escape(package['current_outcome'])} & "
            f"{len(package['observables'])} & {len(package['controls'])} & "
            f"{len(package['energy_accounting']['channels'])} & "
            f"{len(package['missing_required_evidence'])} \\\\"
        )
    (GENERATED_ROOT / "review_admission_rows.tex").write_text(
        "\n".join(rows) + "\n\\bottomrule\n", encoding="ascii"
    )


def generate_beta_result_rows(beta_results: dict[str, Any]) -> None:
    beta_effects = [
        float(record["comparisons"]["beta_to_f_plane_relative_vorticity_l2"])
        for record in beta_results["records"]
    ]
    quotient_effects = [
        float(record["comparisons"]["quotient_to_identity_maximum_vorticity_error"])
        for record in beta_results["records"]
    ]
    budget_residuals = [
        float(arm["energy_budget_residual"])
        for record in beta_results["records"]
        for arm in record["arms"].values()
    ]
    enstrophy_residuals = [
        float(arm["enstrophy_budget_residual"])
        for record in beta_results["records"]
        for arm in record["arms"].values()
    ]
    rows = [
        f"Beta-plane versus f-plane relative vorticity $L^2$ & {min(beta_effects):.6f} & {max(beta_effects):.6f} & Nonzero in every configuration \\\\",
        f"Quotient filter versus identity maximum error & {min(quotient_effects):.1e} & {max(quotient_effects):.1e} & Exact negative control \\\\",
        f"Energy-budget absolute residual & {min(budget_residuals):.2e} & {max(budget_residuals):.2e} & All preregistered bounds pass \\\\",
        f"Enstrophy-budget absolute residual & {min(enstrophy_residuals):.2e} & {max(enstrophy_residuals):.2e} & All preregistered bounds pass \\\\",
    ]
    (GENERATED_ROOT / "review_beta_result_rows.tex").write_text(
        "\n".join(rows) + "\n\\bottomrule\n", encoding="ascii"
    )


def generate_beta_production_rows(beta_results: dict[str, Any]) -> None:
    """Render the four locked beta-five and beta-ten primary contrasts."""
    metric_labels = {
        "final_window_mean_zonal_fraction": "Zonal-energy fraction",
        "persistent_jet": "Persistent-jet prevalence",
    }
    rows = []
    for record in beta_results["primary_contrasts"]:
        if record["beta"] not in {5.0, 10.0}:
            continue
        rows.append(
            f"{metric_labels[record['metric']]} at $\\beta={record['beta']:g}$ & "
            f"{record['effect_estimate']:.4f} & {record['familywise_ci_lower']:.4f} & "
            f"{record['familywise_ci_upper']:.4f} & Not supported \\\\"
        )
    (GENERATED_ROOT / "review_beta_result_rows.tex").write_text(
        "\n".join(rows) + "\n\\bottomrule\n", encoding="ascii"
    )


def main() -> int:
    configure_plots()
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)

    claims_payload = load_json("unified_framework_claims.json")
    gate_results = load_json("claim_gate_results.json")
    overlap = load_json("framework_overlap_audit.json")
    decomposition = load_json("document_decomposition_audit.json")
    beta_results = load_json("beta_plane_sweep_results.json")
    cayley_audit = load_json("cayley_dickson_property_audit.json")
    admission = load_json("experimental_admission_packages.json")
    claims = cast("list[dict[str, Any]]", claims_payload["claims"])

    generate_claim_status_figure(claims)
    generate_framework_overlap_figure(overlap)
    generate_evidence_flow_figure(
        len(claims),
        int(decomposition["document_count"]),
        int(gate_results["gate_count"]),
        int(gate_results["consistent_count"]),
    )
    generate_beta_ablation_figure(beta_results)
    generate_claim_status_rows(claims, gate_results)
    generate_cayley_property_rows(cayley_audit)
    generate_admission_rows(admission)
    generate_beta_production_rows(beta_results)
    print("Generated 4 evidence figures and 4 paper tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
