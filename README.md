# Predicting Next-Hour Waste Heat Availability in a Data Center

**MECH 658 — Introduction to Machine Learning**  
American University of Beirut  
**Nkezi Emmanuel Akofor** · nna56@mail.aub.edu

## Project overview

Can recent computing power and coolant measurements improve next-hour average waste-heat forecasts beyond past heat alone? This project uses Frontier's 2023 operating data to investigate that question. The goal is at least a **10% reduction in test MAE relative to persistence**, alongside a comparison of heat-only and operating-variable models on identical target hours.

**Current status:** data exploration and the persistence baseline are complete. Learned models are planned; test errors have not been calculated.

## Repository files

| File | Purpose |
|---|---|
| `analyze_frontier.py` | Load and check the data, create hourly examples and plots, and evaluate persistence. |
| `baseline.ipynb` | Full analysis code in a self-contained Jupyter/Colab notebook. |
| `requirements.txt` | Pinned dependencies for reproducing the baseline. |
| `README.md` | Project overview, setup, running instructions and baseline results. |

## Dataset

Use **Frontier HPC & Facility Data**, released by Grant and colleagues at Oak Ridge National Laboratory: [Figshare dataset, version 4](https://doi.org/10.6084/m9.figshare.24391240), licensed under **CC BY 4.0**.

The workbook contains 49,869 records and 18 columns for 2023 at approximately ten-minute intervals. This project selects waste heat (MW), computing power (MW), supply and return temperatures (degrees Celsius), and coolant flow (gallons/minute). The target is the following hour's average waste heat in MW.

Download the original workbook and place it beside `analyze_frontier.py`, using the filename **`Frontier HPC & Facility Data.xlsx`**. The dataset is not included in this repository.

Dataset documentation: Sun et al. (2024), *Energy dataset of Frontier supercomputer for waste heat recovery*, Scientific Data. [Paper](https://doi.org/10.1038/s41597-024-03913-w).

## Setup and run

1. Install **Python 3.11 or newer**. Download this repository using **Code → Download ZIP**, then extract it.
2. Put the dataset workbook in the extracted folder.
3. Open a terminal in that folder and install the dependencies:

```sh
python -m pip install -r requirements.txt
```

4. Run the analysis:

```sh
python analyze_frontier.py --data "Frontier HPC & Facility Data.xlsx" --out results
```

If the workbook is elsewhere, replace the filename after `--data` with its full path in quotation marks. The baseline runs on a CPU and does not require a GPU.

## Run in Google Colab instead

Open [Google Colab](https://colab.research.google.com/), choose **File → Upload notebook**, and select `baseline.ipynb`. Upload the original Excel workbook through the notebook’s Files panel. Run the cells from top to bottom. This notebook includes the complete analysis code and does not require `analyze_frontier.py`.

## Preprocessing and evaluation

The script removes the units row, checks timestamp uniqueness, and rounds subsecond offsets to the nearest ten-minute mark. Each retained hour needs six valid measurements for all five variables. Input and target hours must be consecutive and complete. Missing hours are not interpolated; recorded zero values are retained. This leaves **8,256 complete hours** out of 8,760; return temperature has 122 missing original measurements.

Target hours define the chronological split:

| Split | Period in 2023 | Use |
|---|---|---|
| Training | January–August | Fit future learned models; describe baseline errors. |
| Validation | September–October | Select future model settings and compare models. |
| Test | November–December | Final evaluation after models and settings are frozen. |

Persistence predicts that next hour's average waste heat equals the preceding hour's average. It has no fitted parameters. The five-variable completeness rule ensures eligibility is consistent with the planned multivariable comparison, although persistence itself uses only past heat.

## Completed baseline results

| Period | Examples | MAE (MW) | RMSE (MW) |
|---|---:|---:|---:|
| Training | 5,293 | 1.493 | 2.197 |
| Validation | 1,452 | 1.430 | 2.118 |

Training-period errors are descriptive. **No test errors have been calculated.** MAE is the primary metric; RMSE gives greater weight to large errors.

Running the script creates `results/` containing:

- `baseline_metrics.csv`: training and validation persistence scores.
- `raw_statistics.csv`: descriptive statistics for the five selected variables.
- `hourly_data.csv` and `one_hour_examples.csv`: processed data and labelled examples.
- `exploration.pdf` and `exploration.png`: training/validation plots.
- `analysis_summary.json`: data checks, metrics and software versions.

## Next steps

Implement linear regression from scratch and a ridge variant; compare heat-only, individual additional variables, and all five inputs using one-hour and three-hour histories. Then investigate a compact 1D CNN and an optional GRU. LSTM/Transformer training is conditional on time; random forest is a fallback.

Future experiments will use training-only scaling and common eligible target hours. Neural models will use PyTorch with validation-MAE early stopping and three fixed seeds. Scikit-learn and PyTorch will be added when those experiments are implemented. Progress report: **17 November**; poster: **4 December**; final report: **10 December 2026**. The full methodology and weekly timeline are in the project proposal.

## Scope

The target is source-side thermal power. Delivered building heat also depends on temperatures, equipment and demand. Results from one facility and one year may not generalize to other operating conditions; this offline forecast study does not measure energy savings or control performance.

## Software

The current script uses [NumPy](https://numpy.org/), [pandas](https://pandas.pydata.org/), [Matplotlib](https://matplotlib.org/) and [openpyxl](https://openpyxl.readthedocs.io/). Versions are pinned in `requirements.txt` and recorded at runtime. Full paper and software references are provided in the proposal.
