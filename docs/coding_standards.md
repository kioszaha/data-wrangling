## Structure: Organising Folders, Files & Output

1. Data is stored in its own folder separated by airbnb and bonds files.

2. Our Python functions are organised on a deliverable basis. Lecture notes suggest using lots of smaller files. One python file per deliverable is sufficient because each function only serves one purpose. Functions that get reused have been placed in utils folder. e.g. sync_data.py

3. The repository has one clear output folder that contains all the outputs from each deliverable, including csv, pdf, png, and text files.

## Coding Practices

Parameters are clearly defined at the start of the file with no magic numbers. Follow best practice coding conventions including uppercase variable names for constant parameters.

All our python scripts use variables to reference relative file paths in our repository instead of hard coding values.

Fixes:

1. The Christchurch Central area code (326600) was previously hardcoded in a couple places in deliverable_5.py. Replaced with a single constant variable (CHRISTCHURCH_CENTRAL_AREA_CODE) because keeps code working if the value changes in the future.

2. The R markdown code from deliveable 3 hardcoded it's output. Fixed by using the OUTPUT_DIR variable because it stays consistent with how the rest of the file handles paths.

## Code Comments

Code comments are used to explain non-obvious choices made during development and any data caveats.
Additionally comments are used to communicate structure of deliverable tasks for tutor's benefit.

Reviwed comments against notes and already following recommended best practice, no changes needed.

## Example of Sanity Check in Pipeline

In deliverable 5 we have a `fetch_coodinates()` function that maps Airbnb latitude/longitude pairs
to Statistical Area 2 codes using the Koordinates **SA2 2019** layer (`LAYER_ID = 98970`,
`AREA_FIELD = "SA22019_V1_00"`). This is the step most able to quietly return a wrong answer, so it
carries its own check. Once the lookup is merged back into the listings it reports the unresolved
share and refuses to write anything if it is too high:

```python
missing = df["area_code"].isna().sum()
print(f"[green]Missing area codes: {missing} ({missing / len(df):.2%})")
if missing / len(df) > MAX_MISSING_RATIO:
    raise RuntimeError(...)
```

The point of the check is the _ordering_, not the threshold. An invalid API key or rate limiting
produces a table that is still the right shape and the right row count — every listing comes back,
it just has no area code. Written straight to the cache, that result is indistinguishable from a
good one and every later stage (the join, all four analyses) would quietly be wrong. Raising before
the write means a bad run costs one API call, not a full analysis.

Actual output from a clean end-to-end run:

```text
Mapping Airbnb coordinates to area codes...
All coordinates already mapped in destination file. Skipping pool execution.
Missing area codes: 0 (0.00%)
➡️ Saved enriched Airbnb data to ...\.output\cleaned_listings_with_area_code.csv
```

A second, independent check runs at the end of deliverable 5: `sqlite_join()` re-expresses the
same join in SQL and both must agree. They do — 13,852 rows and a $239.00 Christchurch Central
median from both pandas and SQLite.

## Further Cleanups

Integrated the deliverable 3 workflow and plots that were originally built in RStudio as an R Markdown file into the Python pipeline using the rpy2 package. The subsequent graphs now correctly appear in the output folder. This was later changed to call `Rscript` as a separate process instead of `rpy2`, because `rpy2` failed to load R on machines where the Python and R builds differ in architecture (e.g. x64 Python with ARM64 R). The plots step now also treats "PDF was written" as success and never stops the rest of the pipeline.

## Second review pass (revisiting the code against the lectures)

Re-reading the modules against the Week 9 material turned up four things worth changing. All were
about values being _repeated_ or _unexplained_ rather than about style, and the reasoning is
recorded here at the same level of detail as the first pass.

1. **A constant had been re-hardcoded.** The Christchurch Central area code was fixed in pass one,
   but it had since been typed back in as a literal inside the SQL median query — the one place a
   `grep` for the constant would not find. The query now builds it from
   `CHRISTCHURCH_CENTRAL_AREA_CODE`, so the single-source-of-truth rule holds for the code as it
   stands rather than as it once stood.

2. **The remaining magic numbers that actually carry meaning.** The stated standard is "no magic
   numbers", but a literal `7` dividing a weekly rent and a literal `0.05` setting the geocoding
   abort threshold both change results if changed, so they are now `NIGHTS_PER_WEEK`,
   `MAX_MISSING_RATIO`, `MAX_ATTEMPTS` and `GEOCODE_WORKERS`. Trivial integers — loop indices, the
   chunk size — were deliberately left inline, because naming everything is its own kind of noise.

3. **Paths and the snapshot window moved to the top of `deliverable_4.py`.** The file names and the
   `2025-10-05` / `2026-06-19` snapshot bounds were previously written inside the functions that
   used them. They are now `COMBINED_LISTINGS_FILE`, `BONDS_FILE`, `SNAPSHOT_START` and
   `SNAPSHOT_END` alongside the two output paths, so the whole stage's contract is readable in one
   screen.

4. **Module docstrings for the three remaining modules.** `main.py`, `config.py` and
   `file_explorer.py` were the only files without one. Added for consistency — a practice that is
   followed in four files and skipped in three is not a practice.

5. **The design principles document was wrong about the pipeline.** Its join row count, distinct
   area count, dictionary size and an SA2 vintage caveat were all incorrect, so they have been
   corrected against a fresh run. The details are in
   [`design_principles.md`](design_principles.md) under "Findings recorded in this review". Worth
   noting for its own sake: the code was right in every one of those cases and the document was
   wrong, which is the reverse of the usual risk. A document that quotes numbers should have those
   numbers regenerated by a run, not copied forward between write-ups.
