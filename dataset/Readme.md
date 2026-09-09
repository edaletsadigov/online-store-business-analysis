# Dataset

Three relational log files from an online store, covering **June 1, 2017 – May 31, 2018** (12 months). Together they let you trace a user from their first visit, through marketing attribution, to purchase.

| File | Rows | Columns | Purpose |
|---|---|---|---|
| `visits_log_us.csv` | 359,400 | 5 | Every website session |
| `orders_log_us.csv` | 50,415 | 3 | Every completed purchase |
| `costs_us.csv` | 2,542 | 3 | Daily marketing spend per traffic source |

No missing values and no fully duplicated rows in any of the three files.

---

## `visits_log_us.csv` — session log

One row = one visit (session) to the site.

| Original column | Renamed to | Type | Description |
|---|---|---|---|
| `Device` | `device` | string | `desktop` or `touch` — device used for the session |
| `End Ts` | `end_ts` | datetime | Session end timestamp |
| `Source Id` | `source_id` | int | Marketing/traffic source ID (9 unique sources) |
| `Start Ts` | `start_ts` | datetime | Session start timestamp |
| `Uid` | `uid` | uint64 | Unique user ID |

- 228,169 unique users.
- Two rows had `end_ts` earlier than `start_ts` (negative duration); these were clipped to 0 seconds rather than dropped, since the rest of the row is still usable.
- `session_duration_sec`, `session_date`, `session_week`, and `session_month` are derived columns added during cleaning — not present in the raw file.

## `orders_log_us.csv` — purchase log

One row = one completed order.

| Original column | Renamed to | Type | Description |
|---|---|---|---|
| `Buy Ts` | `buy_ts` | datetime | Order timestamp |
| `Revenue` | `revenue` | float | Order value |
| `Uid` | `uid` | uint64 | Unique user ID (joins to `visits_log_us.csv`) |

- 36,523 unique buyers placed 50,415 orders (≈1.38 orders per buyer).

## `costs_us.csv` — marketing spend log

One row = spend on one traffic source on one day.

| Original column | Renamed to | Type | Description |
|---|---|---|---|
| `source_id` | `source_id` | int | Marketing/traffic source ID (7 unique sources here) |
| `dt` | `dt` | datetime | Calendar date |
| `costs` | `costs` | float | Amount spent that day on that source |

- Total marketing spend across the year: **$329,131.62**.
- Only 7 of the 9 `source_id` values from the visits log appear here — sources without a row in this file have no tracked ad spend (e.g. organic/referral channels), which matters when computing CAC.

---

## Joining the tables

- `visits_log_us.csv.uid` ↔ `orders_log_us.csv.uid` — links a user's sessions to their purchases.
- `visits_log_us.csv.source_id` / `costs_us.csv.source_id` — links a session's traffic source to what was spent acquiring it.

## Preparation steps applied

1. Renamed all columns to `snake_case`.
2. Converted all timestamp/date columns to proper `datetime` with `pd.to_datetime`.
3. Clipped the two negative session durations to 0.
4. Derived helper columns (`session_duration_sec`, month/week periods, cohort keys) used for the metrics in [`/charts`](../charts).

Full step-by-step cleaning code is in [`/notebook`](Businnes_analysis_ədalət_sadıqov.ipynb).

