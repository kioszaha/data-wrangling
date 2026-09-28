# 🧭 Design Principles

Team KIOSZAHA — Airbnb vs long-term rental analysis, Christchurch City.

What the pipeline consumes, what it produces, how it runs, and the software strategies behind it.

---

## 1. 📥 Inputs

All inputs live in `.data/`, which is git-ignored and filled by `sync_data()` rather than
committed. Nothing in it is edited by hand.

| Input | Source | Shape | Notes |
| --- | --- | --- | --- |
| `airbnb/listings_YYYYMMDD.csv` × 9 | [Inside Airbnb](https://insideairbnb.com/new-zealand/), mirrored on the team CDN | 18 columns each | Monthly snapshots, 5 Oct 2025 – 19 Jun 2026. The date in the filename is the publication date and is the **only** source of the snapshot date. |
| `bonds/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv` | [Tenancy Services / MBIE](https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/), CC-BY 3.0 NZ | 226,080 rows × 12 columns | Quarterly bond lodgement statistics. `TimeFrame` holds each quarter's **start** date. |
| `sa2_2026_dictionary.json` | Stats NZ SA2 **2026** codes | 2,396 entries | Maps area code → area name, for display only — never used as a join key. The vintage difference against the 2019 codes produced by geocoding does not bite in practice: all 177 codes the pipeline actually produces are present in it, and the `Unknown` fallback in `add_location_names()` covers it if that ever stops being true. |
| `KOORDINATES_API_KEY` | [Koordinates](https://koordinates.com/my/api/), read from `.env` | secret | Required by Deliverable 5 to geocode listings. Without it the run aborts rather than producing partial results. |

Column meanings and cleaning decisions are documented separately in [`airbnb.md`](airbnb.md)
and [`bonds.md`](bonds.md).

**Input contract.** Inputs are immutable and the remote copy is authoritative. `sync_data()`
checks each local file's MD5 against the remote ETag and re-downloads on mismatch, so a
corrupted or hand-edited file repairs itself on the next run.

---

## 2. 📤 Outputs

All outputs land in `.output/`, also git-ignored. The directory rebuilds completely from
`.data/` plus an API key, so it is a build artefact rather than source.

| Output | Produced by | Contents |
| --- | --- | --- |
| `combined_listings.csv` | Deliverable 3 | All nine snapshots filtered to Christchurch City and concatenated, with `published_month` / `published_year` added. 28,795 rows × 20 columns. |
| `summary.md` | Deliverable 3 | Per-column summary statistics and missing-value counts, as a Markdown table. |
| `test_combined_listings_graphs.pdf` | Deliverable 3 | The four plots reproduced from last week's R Markdown workflow. **Conditional:** only written when a working R installation is detectable, otherwise the step logs that it is skipping. |
| `cleaned_listings.csv` | Deliverable 4 | The above, cleaned. 18,119 rows × 17 columns. |
| `cleaned_bonds.csv` | Deliverable 4 | Bond rows for quarters overlapping the snapshot window, plus a derived numeric `beds_num`. 27,118 rows × 13 columns. |
| `cleaned_listings_with_area_code.csv` | Deliverable 5 | Cleaned listings with an SA2 2019 `area_code` geocoded from latitude/longitude. 18,119 rows, 177 distinct areas, 0 unresolved. Doubles as the **geocoding cache**. |
| `joined_listings_bonds.csv` | Deliverable 5 | Inner join of listings and bonds on area code + quarter. 13,852 rows; the 4,267 unmatched listings (23.6%) are in areas or quarters the bond file has no record for. |
| `gap_by_area.csv` / `.png` | Deliverable 5 | Short-term vs long-term nightly price gap per area, and a box plot of the top 10. The CSV is the authoritative ranking: the plot trims the most extreme 1% at each end for legibility, which shifts a box's drawn median slightly away from the `median_gap` it was ranked on. |
| `counts_by_area.csv` / `.png` | Deliverable 5 | Average Airbnb listings vs active long-term rentals per area, and a paired bar chart. |
| `airbnb_bonds.db` | Deliverable 5 | SQLite database holding both cleaned tables, used to reproduce the join in SQL. |

Each stage also prints a colour-coded audit trail: every filter reports how many rows it
removed and what percentage that was, so the full row-count arithmetic can be followed from
the console alone.

---

## 3. 🔁 Main pipeline steps

`main.py` runs four stages in a fixed order. Each stage reads only what the stages before it
wrote, so the order is also the dependency chain.

```
sync_data()  →  deliverable_3()  →  deliverable_4()  →  deliverable_5()
  download       combine            clean              geocode, join, analyse
```

### Step 0 — Download the data (`utils/sync_data.py`)

Fetches the file list from the team CDN and downloads anything missing or changed, checked
by MD5. Two safeguards:

- Files download to a `.tmp` name and are renamed only once complete, so an interrupted run
  never leaves a half-written CSV behind.
- Remote filenames are checked with `is_safe_path()` before use, so nothing can be written
  outside `.data/`.

### Step 1 — Combine the snapshots (`deliverables/deliverable_3.py`)

Turns nine month files (Oct 2025 to June 2026) into one dataset:

1. Find every `listings_YYYYMMDD.csv` and read the snapshot date from its filename.
2. Keep only rows where `neighbourhood_group` is `"Christchurch City"`.
3. Add `published_month` and `published_year` from the snapshot date.
4. Concatenate all nine into `combined_listings.csv` (28,795 rows).
5. Write `summary.md` — per-column statistics, chosen by column type: dates get min/max/mean,
   numbers also get standard deviation, and text columns get their unique count and three
   most common values.
6. Re-run last week's R plots over the combined file via `rpy2` (Task 8 of the brief). This is
   the one step with an external runtime dependency: if R is not installed the import fails,
   the step says so and returns, and the rest of the pipeline continues unaffected.

IDs and coordinates are left out of the summary, since an average `host_id` or latitude means
nothing.

### Step 2 — Clean both datasets (`deliverables/deliverable_4.py`)

Each dataset is cleaned separately, and every filter prints how many rows it removed and what
percentage that was.

**Airbnb** (28,795 → 18,119 rows):

- Drop three columns: `neighbourhood_group` (always the same value), `license` (entirely
  empty) and `host_name` (`host_id` already identifies the host).
- Drop rows with no coordinates, no `minimum_nights` (37 rows), or a missing/zero price
  (10,639 rows).
- Fill missing `reviews_per_month` with 0 — a missing value here means the listing has no
  reviews.
- Parse `last_review` into a real date.

**Bonds** (226,080 → 27,118 rows):

- Keep only quarters that overlap the Airbnb window (5 Oct 2025 – 19 Jun 2026). `TimeFrame`
  holds the quarter's *start* date, so `QuarterEnd(0)` is used to catch Q4 2025, which starts
  before the window but overlaps it.
- Drop rows with no `Location Id` or no `Median Rent`.
- Add a numeric `beds_num` column, mapping `ALL` and `5+` to missing. The original
  `Number Of Beds` text column is kept, so both the categorical and numeric views stay
  available.

### Step 3 — Geocode, join and analyse (`deliverables/deliverable_5.py`)

**Geocode.** Each of the 3,789 unique latitude/longitude pairs is sent to the Koordinates SA2
2019 layer to get its area code — deduplicated first, looked up across 8 parallel processes,
retried up to three times on failure. Results are cached in the output file, so a rerun only
looks up coordinates it hasn't seen; on a rerun with a warm cache the process pool is never
started and the step completes without a single API call. If more than 5% fail to resolve the
stage stops and writes nothing, so a bad API key can't fill the cache with blanks.

*Caveat:* the cache is keyed on coordinates alone and carries no record of which layer produced
it. Changing `LAYER_ID` therefore does **not** invalidate it — the cached file must be removed
or renamed by hand, or the next run will silently reuse codes from the previous layer.

**Join.** Each listing's month is converted to its quarter, then listings are inner-joined to
the bonds on area code + quarter, giving **13,852 rows**. The join is inner because comparing
prices needs both sides present.

**Analyse.** Four questions:

| Question | Method |
| --- | --- |
| Median Airbnb price in Christchurch Central | Median `price` for area 326600 |
| Which areas have the biggest short- vs long-term gap? | Airbnb nightly price minus (weekly rent ÷ 7), areas with ≥10 listings |
| How do Airbnb and rental counts compare? | Average listings per quarter vs average active bonds |
| Airbnb units vs long-term rental beds (bonus) | `beds_num × Active Bonds`, summed per area |



**Cross-check in SQL.** Both cleaned tables are loaded into SQLite and the join is rewritten
as a SQL query. This isn't duplication — it's a correctness check. The SQL join returns
**13,852** rows and a Christchurch Central median of **$239.00**, both exactly matching the
pandas results, confirming the merge keys behave the same way in either implementation.

---

## 4. 🛠️ Coding and software strategies

### Code, data and output are kept in separate places

The repository is split three ways, and the boundary is enforced by `config.py` rather than by
convention alone:

```
data-wrangling/
├── .data/          ← inputs only. Never written to except by sync_data()
│   ├── airbnb/         listings_20251005.csv … listings_20260619.csv
│   ├── bonds/          Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv
│   └── sa2_2026_dictionary.json
├── .output/        ← generated artefacts only. Safe to delete at any time
├── config.py       ← the only place paths are defined
├── main.py         ← orchestration only
├── utils/          ← reusable infrastructure
└── deliverables/   ← analysis, one module per deliverable
```

Each input also lives in its own subdirectory by source — `.data/airbnb/` holds the nine
monthly snapshots, `.data/bonds/` the tenancy file — so `AirbnbListings` can discover every
snapshot with a single `rglob("*.csv")` without tripping over unrelated files.

**Raw data is never modified.** No deliverable writes to `.data/`; only `sync_data()` does, and
only to replace a file whose checksum no longer matches the source. Every transformation reads
from `.data/` and writes to `.output/`. This keeps the raw data auditable: any figure in the
report can be traced back to an untouched original, and deleting `.output/` entirely and
re-running is guaranteed to reproduce it. A pipeline that edits its inputs in place destroys
that guarantee after the first run.

### Paths are derived from the project root, never hard-coded

`config.py` computes the root once and everything hangs off it:

```python
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / ".data"
OUTPUT_DIR = BASE_DIR / ".output"
```

Because `BASE_DIR` comes from `__file__` rather than the current working directory, the
pipeline behaves identically whether it is run from the project root, from inside
`deliverables/`, or from an IDE with a different working directory. There is not a single
absolute path such as `C:\Users\...` anywhere in the codebase, which is what makes the project
portable across the team's Windows and macOS machines. Paths are built with `pathlib`'s `/`
operator rather than string concatenation, so the separator is correct on both.

### Parameters are named, visible, and gathered at the top of the file

Values that might need changing are lifted out of the code that uses them and declared as
module-level constants, so they can be found and edited without reading the logic:

```python
LAYER_ID = 98970                    # deliverable_5.py
AREA_FIELD = "SA22019_V1_00"
API_URL = "https://koordinates.com/services/query/v1/vector.json"
MIN_LISTINGS = 10        # ignore tiny areas when ranking the price gap
MAX_MISSING_RATIO = 0.05 # abort geocoding above this share of unresolved rows
GEOCODE_WORKERS = 8      # parallel lookups; the API is the bottleneck, not the CPU

DATA_URL = "https://data-wrangling-cdn.oskar.nz"   # sync_data.py
```

`MIN_LISTINGS = 10` is the clearest illustration: buried inline as a bare `10` inside a
`.query()` call it would be an unexplained magic number, but named and commented at the top of
the file it is a documented, reviewable analytical choice. The same applies to `LAYER_ID` —
because it is a named constant rather than a literal inside the request, switching SA2 vintages
was a one-line change.

The rule is applied to values that carry meaning, not to every integer. Loop indices, buffer
sizes and the constant `10` in a percentile calculation stay inline. The test applied on review
was: *could a reader change this value to get a different analysis, or be misled about what the
code is doing?* A `10` inside `quantile(0.1)` answers no; a `7` dividing a weekly rent to make it
nightly would answer yes, so it is now `NIGHTS_PER_WEEK`.

The same single-source-of-truth rule applies to data as well as settings: the SA2 name lookup
is loaded once in `main()` and passed down, rather than each function re-reading the JSON.

### Modules carry headers explaining their purpose

Every module now opens with a docstring stating what the file does and, where useful, how to
read it. `deliverable_5.py` documents its own call order so a reader knows where to start:

```python
"""
Deliverable 5: attach SA2 area codes to the Airbnb listings (Koordinates Query API),
join with the bond data, and answer the questions in the brief.

Run order: main()  ->  join_datasets()  ->  the four analysis functions.
"""
```

`deliverable_4.py` and `sync_data.py` do the same, the latter also recording its author.
`main.py`, `config.py` and `file_explorer.py` were added in this pass for consistency — the
practice is only worth following if it is universal, and a reader landing in `config.py` should
immediately learn that it exists to make every other path in the project portable.

### Code is self-documenting

Names are chosen so that the logic reads as a description of itself and needs no accompanying
comment. Variables state what they hold, including their units where that matters:

| Name | Why it works |
| --- | --- |
| `long_term_daily_rate` | States the unit. `rent / 7` alone would leave the reader guessing whether it was weekly or nightly. |
| `airbnb_per_100_rentals` | The column header is the definition — no lookup needed to interpret the number. |
| `coords_to_query` | Distinguishes the coordinates still needing a lookup from `cached_lookup` and `unique_coords`, three similar sets that would otherwise blur together. |
| `rows_lost_timeframe` | Says both what was counted and which filter produced it. |
| `invalid_prices` | A boolean mask named for the condition it encodes, so `df[~invalid_prices]` reads as plain English. |

Functions follow the same rule: `filter_christchurch()`, `month_to_quarter_start()`,
`summarise_column()` and `is_safe_path()` each state their effect precisely enough that a
reader can follow `main()` end to end without opening any of them. `is_safe_path()` is the
useful case — a name like `check_path()` would not have conveyed that a *security* property is
being asserted.


### Fail fast, with actionable errors

Every stage checks its inputs up front and raises with
a message that says what to do — `FileNotFoundError(f"{INPUT_FILE} does not exist. Did you run
deliverable_3()?")` — instead of letting a missing file surface later as a confusing `KeyError`.
Geocoding adds a quality threshold: above 5% unresolved, it raises and writes nothing.

### Comments explain *why*, not *what*

Comments are reserved for decisions a reader could not infer from the code itself. The example
is in `compare_property_counts()`, above the choice of which bond column to count:

```python
# Both sides as an average count per quarter. Active Bonds is the stock of
# tenancies in force; Total Bonds is only NEW bonds lodged in the quarter
# (a flow), so summing it would measure turnover, not how many properties.
rental_counts = bonds_all.groupby("Location Id")["Active Bonds"].mean()
```

The code says *what* it does — group and average. What it cannot say is why `Active Bonds` and
not `Total Bonds`, when both are plausible columns with similar names. Picking the wrong one
would have produced a number that ran without error, looked entirely reasonable, and answered
a different question: how much tenancy churn an area has, rather than how many rentals exist in
it. The comment records the distinction so the next person cannot quietly undo it.


### Secrets and data out of version control

The API key is read from `.env` and never appears
in source. `.data/` and `.output/` are git-ignored — raw data rebuilds from the CDN and derived
data rebuilds from the pipeline, so committing either would bloat the repo while risking a
stale copy being mistaken for current.


### Validation over assumption

Where a result could be wrong while still running, it gets checked rather than trusted. The
example is `sqlite_join()`, which re-expresses the central join a second time in a different
language and compares the answers:

```sql
SELECT l.*, b."Median Rent", b."Total Bonds", b."Active Bonds"
FROM listings AS l
INNER JOIN bonds AS b
    ON l.area_code = b."Location Id" AND l.TimeFrame = b.TimeFrame
```

A merge on two keys is exactly the kind of operation that fails quietly: a dtype mismatch or a
stray whitespace in a key silently drops rows, and the result is a smaller table that still
looks perfectly valid. Running the same join through pandas and through SQLite and requiring
both to agree turns that silent failure into a visible one. Both currently return **13,852**
rows and a Christchurch Central median of **$239.00**, which is evidence the merge keys behave
as intended — not merely an assumption that they do.

Note that the area code in the SQL median query is interpolated from
`CHRISTCHURCH_CENTRAL_AREA_CODE` rather than typed as a literal. That constant exists precisely
because a hardcoded `326600` was duplicated in three places; re-introducing it inside a string
literal is how the duplication comes back, and a raw literal in SQL is invisible to a reader
grepping for the constant.

### Findings recorded in this review

The figures quoted in this document were re-derived from a clean end-to-end run rather than
carried forward from the previous write-up. Four of them were wrong, and all four were
overstatements of how well the pipeline was doing:

- The join produces 13,852 rows, not the 15,462 previously stated. 23.6% of listings go
  unmatched, not 14.7%. The SQL cross-check still agreed with pandas, so the *code* was right
  and the *document* was stale — which is exactly the failure mode this document exists to
  prevent, and a reason to re-run before editing rather than edit from memory.
- Geocoding resolves 177 distinct areas, not 170.
- The SA2 2026 dictionary has 2,396 entries, not 2,395.
- The 2019-versus-2026 vintage mismatch was documented as a known gap. It is not one: every one
  of the 177 codes produced is present in the dictionary. A speculative caveat reads exactly
  like a measured finding on the page, which is the reason to check rather than assert.

The other change this pass made to the code was a genuine regression: the Christchurch Central
area code had been re-hardcoded inside the SQL median query, undoing the fix described in
`coding_standards.md`. It is now a parameter of the query, built from the constant.

---

## 5. 🤖 AI usage statement

**Claude (Anthropic), via Claude Code**, was used to:

- draft and refactor Python functions, reviewed by team members before merging;
- audit the pipeline against this document and flag inconsistencies (the "Findings recorded in
  this review" section above is the output of that audit, cross-checked against a real run);
- draft this document.

All analytical decisions — which columns to drop, how to handle missing values, how to define
the price gap, and how to interpret results — were made by the team. AI-assisted code went
through the same review rules as hand-written code.

