#!/usr/bin/env python3
"""
Statistical analysis of CPU benchmark results for the JUCE vs raw VST3 SDK comparison.

Expects CSV files named with the pattern:
    results_<plugin><instances>.csv
e.g. results_sdk10.csv, results_juce100.csv

Each CSV has columns: run, cycles, instructions, cache_misses

Usage:
    python3 analyze_benchmarks.py [path_to_csv_directory]

If no directory is given, uses the current directory.
"""

import sys
import re
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


# --------------------------------------------------------------------------
# File discovery & loading
# --------------------------------------------------------------------------

FILENAME_RE = re.compile(r"results_(sdk|juce)(\d+)\.csv$", re.IGNORECASE)


def load_all(directory: Path) -> pd.DataFrame:
    """Load every results_<plugin><n>.csv in the directory into one dataframe.

    Returns a long-format frame with columns:
        plugin, instances, run, cycles, instructions, cache_misses
    """
    rows = []
    for path in sorted(directory.glob("results_*.csv")):
        m = FILENAME_RE.match(path.name)
        if not m:
            print(f"  skipping {path.name} (doesn't match pattern)")
            continue
        plugin = m.group(1).lower()
        instances = int(m.group(2))

        df = pd.read_csv(path)
        df["plugin"] = plugin
        df["instances"] = instances
        rows.append(df)
        print(f"  loaded {path.name}: {len(df)} runs")

    if not rows:
        raise SystemExit(
            "No matching CSV files found. Expected names like results_sdk10.csv"
        )

    return pd.concat(rows, ignore_index=True)


# --------------------------------------------------------------------------
# Summary statistics
# --------------------------------------------------------------------------

def summarize(data: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Mean, median, stddev, coefficient of variation, min, max, n per group."""
    grouped = data.groupby(["instances", "plugin"])[metric]
    summary = grouped.agg(
        n="count",
        mean="mean",
        median="median",
        std="std",
        min="min",
        max="max",
    )
    summary["cv"] = summary["std"] / summary["mean"]
    return summary.round(3)


# --------------------------------------------------------------------------
# Hypothesis testing
# --------------------------------------------------------------------------

def compare_plugins(data: pd.DataFrame, metric: str) -> pd.DataFrame:
    """For each instance count, run Welch's t-test and Mann-Whitney U on sdk vs juce.

    Welch's t-test doesn't assume equal variance, which is the right default here.
    Mann-Whitney U is non-parametric, robust to non-normal distributions.
    Also reports Cohen's d (effect size) and the percent difference of means.
    """
    results = []
    for n_instances in sorted(data["instances"].unique()):
        subset = data[data["instances"] == n_instances]
        sdk = subset[subset["plugin"] == "sdk"][metric].values
        juce = subset[subset["plugin"] == "juce"][metric].values

        if len(sdk) == 0 or len(juce) == 0:
            continue

        # Welch's t-test
        t_stat, t_p = stats.ttest_ind(sdk, juce, equal_var=False)

        # Mann-Whitney U (non-parametric sanity check)
        u_stat, u_p = stats.mannwhitneyu(sdk, juce, alternative="two-sided")

        # Cohen's d with pooled standard deviation
        pooled_std = np.sqrt((sdk.std(ddof=1) ** 2 + juce.std(ddof=1) ** 2) / 2)
        cohens_d = (juce.mean() - sdk.mean()) / pooled_std if pooled_std > 0 else np.nan

        # Percent difference: positive means JUCE used more cycles than SDK
        pct_diff = 100.0 * (juce.mean() - sdk.mean()) / sdk.mean()

        results.append({
            "instances": n_instances,
            "sdk_mean": sdk.mean(),
            "juce_mean": juce.mean(),
            "pct_diff_juce_vs_sdk": pct_diff,
            "cohens_d": cohens_d,
            "welch_t": t_stat,
            "welch_p": t_p,
            "mwu_p": u_p,
            "significant_p<.05": t_p < 0.05,
        })

    return pd.DataFrame(results).round(4)


# --------------------------------------------------------------------------
# Plots
# --------------------------------------------------------------------------

def boxplot(data: pd.DataFrame, metric: str, outfile: Path) -> None:
    """Side-by-side box plot of sdk vs juce at each instance count."""
    instance_counts = sorted(data["instances"].unique())

    fig, ax = plt.subplots(figsize=(10, 6))

    positions = []
    labels = []
    box_data = []
    colors = []

    width = 0.35
    for i, n in enumerate(instance_counts):
        sdk_vals = data[(data["instances"] == n) & (data["plugin"] == "sdk")][metric]
        juce_vals = data[(data["instances"] == n) & (data["plugin"] == "juce")][metric]

        positions.extend([i - width / 2, i + width / 2])
        box_data.extend([sdk_vals, juce_vals])
        colors.extend(["#4C72B0", "#DD8452"])
        labels.extend([f"SDK\nn={n}", f"JUCE\nn={n}"])

    bp = ax.boxplot(box_data, positions=positions, widths=width, patch_artist=True)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticks(range(len(instance_counts)))
    ax.set_xticklabels([f"{n} instances" for n in instance_counts])
    ax.set_ylabel(metric)
    ax.set_title(f"{metric} by plugin and instance count")
    ax.grid(axis="y", alpha=0.3)

    # Custom legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#4C72B0", alpha=0.7, label="SDK"),
        Patch(facecolor="#DD8452", alpha=0.7, label="JUCE"),
    ]
    ax.legend(handles=legend_elements, loc="upper left")

    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"  saved {outfile}")


def means_plot(data: pd.DataFrame, metric: str, outfile: Path) -> None:
    """Mean +/- standard deviation across instance counts.

    Useful for seeing whether any difference scales linearly with instance count,
    which is what we would expect if it is real per-plugin framework overhead.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    for plugin, color in [("sdk", "#4C72B0"), ("juce", "#DD8452")]:
        sub = data[data["plugin"] == plugin]
        agg = sub.groupby("instances")[metric].agg(["mean", "std"]).reset_index()
        ax.errorbar(
            agg["instances"],
            agg["mean"],
            yerr=agg["std"],
            marker="o",
            capsize=4,
            label=plugin.upper(),
            color=color,
            linewidth=2,
        )

    ax.set_xlabel("Instance count")
    ax.set_ylabel(f"Mean {metric} (error bars: 1 std dev)")
    ax.set_title(f"{metric} vs instance count")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"  saved {outfile}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    outdir = directory / "analysis_output"
    outdir.mkdir(exist_ok=True)

    print(f"\nLoading CSVs from: {directory.resolve()}")
    data = load_all(directory)
    print(f"\nTotal runs loaded: {len(data)}")
    print(f"Plugins present: {sorted(data['plugin'].unique())}")
    print(f"Instance counts present: {sorted(data['instances'].unique())}")

    for metric in ["cycles", "instructions", "cache_misses"]:
        print(f"\n{'=' * 70}")
        print(f"Metric: {metric}")
        print("=" * 70)

        summary = summarize(data, metric)
        print("\nSummary statistics:")
        print(summary)

        comparison = compare_plugins(data, metric)
        if not comparison.empty:
            print(f"\nJUCE vs SDK comparison ({metric}):")
            print(comparison.to_string(index=False))

        summary.to_csv(outdir / f"summary_{metric}.csv")
        comparison.to_csv(outdir / f"comparison_{metric}.csv", index=False)

        boxplot(data, metric, outdir / f"boxplot_{metric}.png")
        means_plot(data, metric, outdir / f"means_{metric}.png")

    print(f"\nAll outputs written to: {outdir.resolve()}")
    print("\nQuick interpretation guide:")
    print("  - CV (coefficient of variation) < 0.05 means measurements are tight")
    print("  - welch_p < 0.05 means the difference is statistically significant")
    print("  - Cohen's d: 0.2 = small, 0.5 = medium, 0.8 = large effect")
    print("  - pct_diff positive = JUCE used more cycles than SDK")


if __name__ == "__main__":
    main()
