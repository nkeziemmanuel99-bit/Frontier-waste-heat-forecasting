"""Reproduce the proposal's exploration and persistence baseline (no test scoring)."""
from pathlib import Path
import argparse
import json
import platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openpyxl


def analyze_frontier(data_path, output_directory="results"):
    """Load the workbook, explore hourly data, and score persistence without test scoring."""
    out = Path(output_directory)
    out.mkdir(parents=True, exist_ok=True)

    # The first row below the column names stores units, not a measurement.
    raw = pd.read_excel(data_path, sheet_name="Frontier2023")
    units = raw.iloc[0].astype(str).to_dict()
    data = raw.iloc[1:].copy()
    times = pd.to_datetime(data.pop("Date/Time"), errors="raise")
    rounded = times.dt.round("10min")
    offsets = (times - rounded).dt.total_seconds().abs()
    if offsets.max() >= 1 or rounded.duplicated().any():
        raise ValueError("Inspect timestamps: rounding must stay below 1 second and preserve uniqueness")
    data.index = pd.DatetimeIndex(rounded, name="target_hour")
    data = data.apply(pd.to_numeric, errors="raise").sort_index()
    columns = {"Overall_WasteHeat": "heat_MW", "Frontier Compute Power": "power_MW", "Overall Coolant Supply Temp": "supply_C", "Overall-average Coolant Return Temp": "return_C", "Overall Coolant FLow": "flow_gpm"}
    selected = data[list(columns)].rename(columns=columns)
    selected.describe().T.to_csv(out / "raw_statistics.csv")

    # Keep an hour only if all five variables have all six 10-minute measurements.
    # No interpolation, forward filling, or removal of recorded zero values.
    hourly = selected.resample("h").mean()
    complete = selected.resample("h").count().eq(6).all(axis=1)
    hourly = hourly.where(complete, np.nan)
    hourly.to_csv(out / "hourly_data.csv")

    # A row indexed by t predicts the average during [t,t+1h) from [t-1h,t).
    features = hourly.shift(1).add_prefix("lag1_")
    examples = features.join(hourly["heat_MW"].rename("target_heat_MW")).dropna()
    examples["split"] = np.select([examples.index < "2023-09-01", examples.index < "2023-11-01"], ["train", "validation"], default="test")
    examples.to_csv(out / "one_hour_examples.csv")
    metrics = []
    for split in ["train", "validation"]:
        part = examples.loc[examples["split"] == split]
        error = part["lag1_heat_MW"] - part["target_heat_MW"]
        metrics.append({"split": split, "n": len(part), "MAE_MW": error.abs().mean(), "RMSE_MW": np.sqrt(np.mean(error ** 2))})
    pd.DataFrame(metrics).to_csv(out / "baseline_metrics.csv", index=False)

    # The figure excludes Nov-Dec target values. Do not use test outcomes to tune.
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 2.45), gridspec_kw={"width_ratios": [1.65, 1]})
    for label, start, end, color in [("Train", "2023-01-01", "2023-09-01", "#245c82"), ("Validation", "2023-09-01", "2023-11-01", "#c67b28")]:
        part = hourly.loc[(hourly.index >= start) & (hourly.index < end), "heat_MW"]
        axes[0].plot(part.index, part, lw=0.45, color=color, label=label)
        axes[1].hist(part.dropna(), bins=np.linspace(0, 28, 29), density=True, histtype="step", lw=1.3, label=label, color=color)
    axes[0].set(title="(a) Complete hourly waste-heat averages", ylabel="Waste heat (MW)")
    axes[0].xaxis.set_major_locator(matplotlib.dates.MonthLocator(interval=2))
    axes[0].xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b"))
    axes[1].set(title="(b) Target distribution", xlabel="Waste heat (MW)", ylabel="Density (1/MW)")
    axes[0].legend(frameon=False, loc="upper left", ncol=2, fontsize=8)
    for ax in axes:
        ax.grid(axis="y", alpha=0.18)
    fig.tight_layout()
    fig.savefig(out / "exploration.pdf", bbox_inches="tight")
    fig.savefig(out / "exploration.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    report = {"rows": len(data), "columns": len(data.columns) + 1,
              "complete_hours": int(complete.sum()), "calendar_hours": len(hourly),
              "missing_selected": selected.isna().sum().to_dict(),
              "max_timestamp_offset_seconds": float(offsets.max()),
              "timestamp_offsets_corrected": int((offsets > 0).sum()),
              "zero_heat_records": int(selected.heat_MW.eq(0).sum()),
              "units_original": units, "metrics": metrics,
              "versions": {"Python": platform.python_version(), "numpy": np.__version__,
                           "pandas": pd.__version__, "matplotlib": matplotlib.__version__,
                           "openpyxl": openpyxl.__version__}}
    (out / "analysis_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["rows", "complete_hours", "metrics", "versions"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Frontier exploration and persistence baseline; no test scoring.")
    parser.add_argument("--data", required=True, help="Path to the original Frontier workbook")
    parser.add_argument("--out", default="results", help="Output directory")
    args = parser.parse_args()
    analyze_frontier(args.data, args.out)
