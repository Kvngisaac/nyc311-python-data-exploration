"""Regenerate exact-data Matplotlib figures; exported SVG and PNG are standalone."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

ROOT = Path(__file__).resolve().parent
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.labelcolor": "#43554d", "text.color": "#182f28",
                     "axes.edgecolor": "#bdcdc3", "figure.facecolor": "#ffffff", "savefig.facecolor": "#ffffff", "svg.hashsalt": "nyc311-eda-v1"})


def save(fig, name):
    folder = ROOT / "figures"
    folder.mkdir(exist_ok=True)
    fig.savefig(folder / (name + ".png"), dpi=150, bbox_inches="tight", metadata={"Software": "Matplotlib"})
    fig.savefig(folder / (name + ".svg"), bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)


def main():
    model = json.loads((ROOT / "results/analysis.json").read_text())
    overall = model["views"]["all|all"]
    n = overall["metrics"]["requests"]
    note = "NYC311 · requests created Jan 2024 · pinned Oct 2026 snapshot · descriptive, not causal"
    problems = pd.DataFrame(overall["problems"]).head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.barh(problems["name"], problems["requests"], color="#285a44", height=.64)
    for i, count in enumerate(problems["requests"]):
        ax.text(count + 600, i, f"{count:,} · {count/n:.1%}", va="center", fontsize=10)
    ax.set_xlim(0, problems["requests"].max() * 1.32)
    ax.set_title("What entered the queue?", loc="left", pad=18)
    ax.set_xlabel("Requests created · top 10 problem categories")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    fig.text(.01, -.025, note, fontsize=9, color="#607068")
    save(fig, "problem-volume")
    days = pd.DataFrame(overall["daily"])
    fig, ax = plt.subplots(figsize=(11, 4.8))
    x = list(range(1, 32))
    ax.plot(x, days["requests"], color="#285a44", marker="o", markersize=3)
    ax.fill_between(x, days["requests"], alpha=.10, color="#285a44")
    ax.set_title("Daily intake varies within the month", loc="left", pad=18)
    ax.set_xlabel("January 2024 · local creation date")
    ax.set_ylabel("Requests created")
    ax.set_xticks([1, 5, 10, 15, 20, 25, 31])
    ax.grid(axis="y", alpha=.18)
    fig.text(.01, -.025, note + " · not a full-year seasonality estimate", fontsize=9, color="#607068")
    save(fig, "daily-intake")
    bins = overall["duration_bins"]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar([r["label"] for r in bins], [r["requests"] for r in bins], color=["#285a44"] * 3 + ["#ac7e38"] * 3, width=.62)
    for i, row in enumerate(bins):
        ax.text(i, row["requests"] + 1300, f"{row['requests']:,}", ha="center", fontsize=10)
    ax.set_ylim(0, max(r["requests"] for r in bins) * 1.18)
    ax.set_title("The closure-time distribution has a long tail", loc="left", pad=18)
    ax.set_ylabel("Eligible closed requests")
    ax.set_xlabel("Elapsed UTC-adjusted time to recorded closure · zero durations included")
    fig.text(.01, -.025, f"n={overall['metrics']['timing_eligible']:,}; median {overall['metrics']['median_hours']:.2f} h; p90 {overall['metrics']['p90_hours']:.2f} h. Closed status is not proof of a fix.", fontsize=9, color="#607068")
    save(fig, "closure-distribution")
    missing = sorted(model["quality"]["normalized_missing_count"].items(), key=lambda item: item[1])
    missing = [(field, count) for field, count in missing if count]
    fig, ax = plt.subplots(figsize=(11, 5.7))
    ax.barh([field.replace("_", " ") for field, _ in missing], [count/n*100 for _, count in missing], color="#687d9a", height=.62)
    for i, (_, count) in enumerate(missing):
        ax.text(count/n*100 + 1, i, f"{count:,} · {count/n:.2%}", va="center", fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_title("Missingness is a measurement constraint", loc="left", pad=18)
    ax.set_xlabel("Percent missing after declared null-token normalization")
    fig.text(.01, -.025, "Due date is an expected agency update date in the dictionary, not a universal resolution SLA. No deadline-compliance claim is made.", fontsize=9, color="#607068")
    save(fig, "missingness")
    rows = [r for r in model["same_problem_comparisons"]["HEAT/HOT WATER"] if r["name"] != "Unknown / unassigned"]
    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.barh([r["name"] for r in rows][::-1], [r["median_hours"] for r in rows][::-1], color="#285a44", height=.6)
    for i, row in enumerate(rows[::-1]):
        ax.text(row["median_hours"] + .5, i, f"{row['median_hours']:.2f} h · timed n={row['timing_eligible']:,}", va="center", fontsize=10)
    ax.set_xlim(0, max(r["median_hours"] for r in rows) * 1.55)
    ax.set_title("Compare the same problem before comparing locations", loc="left", pad=18)
    ax.set_xlabel("Median hours to recorded closure · HEAT/HOT WATER requests")
    fig.text(.01, -.025, "Conditional on valid closed records. Different severity, reporting behavior and agency processes are uncontrolled; these are not causal borough rankings.", fontsize=9, color="#607068")
    save(fig, "same-problem-boroughs")
    print("Generated five data figures, each as PNG and SVG.")


if __name__ == "__main__":
    main()
