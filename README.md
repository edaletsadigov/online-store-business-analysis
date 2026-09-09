# Business Analysis — Online Store Product & Marketing Performance

End-to-end business analysis of an online store's user behavior, sales, and marketing efficiency, using one year of session logs (June 2017 – May 2018). The goal is to answer three questions: **how do people use the product, what drives sales, and is marketing spend paying for itself.**

## Repository structure

```
.
├── dataset/          # raw CSV files + column-level documentation
│   ├── costs_us.csv
│   ├── orders_log_us.csv
│   ├── visits_log_us.csv
│   └── README.md
├── charts/            # all Plotly visualizations (PNG + interactive HTML)
│   ├── *.png / *.html
│   ├── generate_charts.py
│   └── README.md
└── business_analysis_edalet_sadigov.ipynb           # full analysis notebook (cleaning → metrics → charts)
└── Readme.md
```

- **[`/dataset`](dataset/README.md)** — what each file contains, column definitions, data quality notes, how the three tables join.
- **[`/charts`](charts/README.md)** — every chart with its interpretation, plus the script to regenerate them.
- **[`/notebook`](notebook)** — the full analysis: data cleaning, metric calculations, and chart-generating code in one place.

## Tech stack

`pandas` · `numpy` · `scipy` · `plotly` (charts exported via `kaleido`)

## Data

Three relational logs covering 12 months:

| File | Rows | What it tracks |
|---|---|---|
| `visits_log_us.csv` | 359,400 | Website sessions (device, source, timestamps) |
| `orders_log_us.csv` | 50,415 | Completed purchases (revenue, timestamp) |
| `costs_us.csv` | 2,542 | Daily marketing spend per traffic source |

No missing values, no duplicate rows. Full documentation in [`dataset/README.md`](dataset/README.md).

## Method

1. **Data cleaning** — renamed columns to snake_case, converted timestamps, corrected two rows with negative session duration.
2. **Product metrics** — DAU/WAU/MAU, sticky factor, session duration and frequency, monthly cohort retention.
3. **Sales metrics** — time-to-first-purchase, monthly order volume, cumulative LTV by acquisition cohort.
4. **Marketing metrics** — spend by source and month, CAC by source, cumulative ROI by cohort against a break-even line.
5. **Cross-check** — Spearman correlation between daily spend and daily revenue, with an explicit correlation-≠-causation flag.

## Key findings

| Metric | Value | Read |
|---|---|---|
| Average DAU / WAU / MAU | 908 / 5,716 / 23,228 | Sticky factor ≈ 3.9% — most users are infrequent visitors |
| Median session length | 300 sec (5 min) | Mean (643 sec) is pulled up by a long tail of longer sessions |
| Month-2 retention | ~7%, settling to 3–5% | Steep early churn, little durable repeat engagement |
| Same-day purchase rate | 72% of buyers | Strong impulse-buying behavior over considered purchases |
| Orders per buyer | 1.38 | Low repeat-purchase rate |
| Total marketing spend | $329,131.62 | Source 3 alone accounts for ~$141K (43%) |
| CAC range across sources | $3.9 – $15.5 | ~4x spread; Source 3 is both highest-spend and least efficient |
| Cohort ROI at 6 months | Best cohorts ~1.3–1.35, none reach 1.0 within 6 months for most | Marketing spend is not recovered quickly for most cohorts |

Full chart-by-chart detail and visuals: **[`charts/README.md`](charts/README.md)**.

## Reproducing this analysis

```bash
pip install pandas numpy scipy "plotly==5.24.1" "kaleido==0.2.1"
```

Then either open the notebook in `notebook/`, or regenerate just the charts:

```bash
cd charts
python generate_charts.py
```

## Author

Ədalət Sadıqov — [GitHub](https://github.com/edaletsadigov) · [LinkedIn](https://linkedin.com/in/edaletsadigov)

