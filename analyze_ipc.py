#!/usr/bin/env python3
"""
Quick IPC analysis for benchmark CSVs.

Looks for files named:
    results_<plugin><instances>.csv
For example:
    results_sdk100.csv
    results_juce100.csv

Expected CSV columns:
    run, cycles, instructions
Optional extra columns are ignored.

The script computes:
    IPC = instructions / cycles

It then writes:
    - summary_ipc.csv
    - comparison_ipc.csv (if both sdk and juce are present)
    - boxplot_ipc.png
    - means_ipc.png

Usage:
    python3 analyze_ipc.py [path_to_csv_directory]

If no directory is given, the current directory is used.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


FILENAME_RE = re.compile(r"results_(sdk|juce)(\d+)\.csv$", re.IGNORECASE)


def load_all(directory: Path) -> pd.DataFrame:
    """Load matching CSVs and return one long-format dataframe."""
    rows = []
    for path in sorted(directory.glob("results_*.csv")):
        match = FILENAME_RE.match(path.name)
        if not match:
            print(f"Skipping {path.name} (name does not match expected pattern)")
            continue

        plugin = match.group(1).lower()
        instances = int(match.group(2))

        df = pd.read_csv(path)
        required = {"cycles", "instructions"}
        missing = required - set(df.columns)
        if missing:
            raise SystemExit(f"{path.name} is missing required columns: {sorted(missing)}")

        df = df.copy()
        df["plugin"] = plugin
        df["instances"] = instances
        df["ipc"] = np.where(df["cycles"] > 0, df["instructions"] / df["cycles"], np.nan)
        rows.append(df)
        print(f"Loaded {path.name}: {len(df)} rows")

    if not rows:
        raise SystemExit("No matching CSV files found. Expected names like results_sdk100.csv")

    return pd.concat(rows, ignore_index=True)


def summarize(data: pd.DataFrame) -> pd.DataFrame:
    """Summary statistics for IPC by instance count and plugin."""
    grouped = data.groupby(["instances", "plugin"])["ipc"]
    summary = grouped.agg(
        n="count",
        mean="mean",
        median="median",
        std="std",
        min="min",
        max="max",
    )
    summary["cv"] = summary["std"] / summary["mean"]
    return summary.round(4)


def compare_plugins(data: pd.DataFrame) -> pd.DataFrame:
    """Compare SDK vs JUCE IPC at each instance count."""
    results = []
    for n_instances in sorted(data["instances"].unique()):
        subset = data[data["instances"] == n_instances]
        sdk = subset[subset["plugin"] == "sdk"]["ipc"].dropna().values
        juce = subset[subset["plugin"] == "juce"]["ipc"].dropna().values

        if len(sdk) == 0 or len(juce) == 0:
            continue

        welch_t, welch_p = stats.ttest_ind(sdk, juce, equal_var=False)
        mwu_u, mwu_p = stats.mannwhitneyu(sdk, juce, alternative="two-sided")

        pooled_std = np.sqrt((sdk.std(ddof=1) ** 2 + juce.std(ddof=1) ** 2) / 2)
        cohens_d = (juce.mean() - sdk.mean()) / pooled_std if pooled_std > 0 else np.nan

        pct_diff = 100.0 * (juce.mean() - sdk.mean()) / sdk.mean()

        results.append({
            "instances": n_instances,
            "sdk_mean_ipc": sdk.mean(),
            "juce_mean_ipc": juce.mean(),
            "pct_diff_juce_vs_sdk": pct_diff,
            "cohens_d": cohens_d,
            "welch_t": welch_t,
            "welch_p": welch_p,
            "mwu_u": mwu_u,
            "mwu_p": mwu_p,
            "significant_p<.05": welch_p < 0.05,
        })

    return pd.DataFrame(results).round(6)


def boxplot_ipc(data: pd.DataFrame, outfile: Path) -> None:
    """Grouped boxplot of IPC by plugin and instance count."""
    instance_counts = sorted(data["instances"].unique())

    positions = []
    box_data = []
    colors = []
    xticks = []

    width = 0.35
    fig, ax = plt.subplots(figsize=(11, 6))

    for i, n in enumerate(instance_counts):
        sdk_vals = data[(data["instances"] == n) & (data["plugin"] == "sdk")]["ipc"].dropna()
        juce_vals = data[(data["instances"] == n) & (data["plugin"] == "juce")]["ipc"].dropna()

        positions.extend([i - width / 2, i + width / 2])
        box_data.extend([sdk_vals, juce_vals])
        colors.extend(["#4C72B0", "#DD8452"])
        xticks.append(i)

    bp = ax.boxplot(box_data, positions=positions, widths=width, patch_artist=True)
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{n} inst." for n in instance_counts])
    ax.set_ylabel("IPC = instructions / cycles")
    ax.set_title("Instructions per cycle by plugin and instance count")
    ax.grid(axis="y", alpha=0.3)

    from matplotlib.patches import Patch
    ax.legend(
        handles=[
            Patch(facecolor="#4C72B0", alpha=0.7, label="SDK"),
            Patch(facecolor="#DD8452", alpha=0.7, label="JUCE"),
        ],
        loc="best",
    )

    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"Saved {outfile}")


def means_plot(data: pd.DataFrame, outfile: Path) -> None:
    """Mean IPC with +/- one standard deviation."""
    fig, ax = plt.subplots(figsize=(11, 6))

    for plugin in ["sdk", "juce"]:
        sub = data[data["plugin"] == plugin]
        if sub.empty:
            continue
        agg = sub.groupby("instances")["ipc"].agg(["mean", "std"]).reset_index()
        ax.errorbar(
            agg["instances"],
            agg["mean"],
            yerr=agg["std"],
            marker="o",
            capsize=4,
            linewidth=2,
            label=plugin.upper(),
        )

    ax.set_xlabel("Instance count")
    ax.set_ylabel("Mean IPC (error bars: 1 std dev)")
    ax.set_title("Mean IPC vs instance count")
    ax.grid(alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.savefig(outfile, dpi=150)
    plt.close()
    print(f"Saved {outfile}")


def main() -> None:
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    outdir = directory / "analysis_output_ipc"
    outdir.mkdir(exist_ok=True)

    print(f"Loading CSVs from: {directory.resolve()}")
    data = load_all(directory)

    print(f"Rows loaded: {len(data)}")
    print(f"Plugins present: {sorted(data['plugin'].unique())}")
    print(f"Instance counts present: {sorted(data['instances'].unique())}")

    summary = summarize(data)
    print("\nSummary statistics:")
    print(summary)

    comparison = compare_plugins(data)
    if not comparison.empty:
        print("\nSDK vs JUCE comparison:")
        print(comparison.to_string(index=False))
    else:
        print("\nNo SDK vs JUCE comparison could be computed (need both plugins present).")

    summary.to_csv(outdir / "summary_ipc.csv")
    comparison.to_csv(outdir / "comparison_ipc.csv", index=False)

    boxplot_ipc(data, outdir / "boxplot_ipc.png")
    means_plot(data, outdir / "means_ipc.png")

    print(f"\nAll outputs written to: {outdir.resolve()}")
    print("IPC = instructions / cycles")


if __name__ == "__main__":
    main()
