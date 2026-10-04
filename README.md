# Team KIOSZAHA : Data Wrangling

## 🛞 Team members:

- 🙀 Oskar Greig

- 🥸 Zaeim Imran Bin Mohd Nazri

- 😎 Oliver Howorth

- Suganya Karthic Kumar

- � ~~Hattie Zhong~~

- � ~~Kiran Rajesh Rajesh Lidiya~~

## 📃 Group rules

### 🪾 Branches

1. **Make a new branch for every change you make to main.** One job per branch!
2. **Run `git checkout main`, `git pull`, and `uv sync` before creating any new branch.**
3. **Prefix your branch with a helpful discriminator:**
   - `docs/*`: **Documentation or rules.** README files, guidelines, API docs, or setup instructions.
   - `task/*`: **New features/tasks.** Adding new scripts, or any new features to existing scripts.
   - `fix/*`: **Bug fixes.** Fix broken code or syntax errors.
   - `refactor/*`: **Cleanup.** Structural or aesthetic changes to existing code.
   - `chore/*`: **Maintenance work.** Updating .gitignore, adding dependencies, etc.

### 🎯 Pull requests & merging

1. **Don't merge your own code.** Create a pull request and message the group chat so another group member can look over your code, provide feedback where necessary, and publish the feature.
2. **Don't merge through the git CLI.** Merge through the [repository page](https://github.com/kioszaha/data-wrangling) on GitHub so you can visually inspect modifications and leave comments where changes may be required.
3. **Let the group know of any new pull requests or merges.** If your change is small and a code review is likely not necessary (e.g, a fix, refactor, or chore), send a message to the group chat letting the group know you merged onto main, what you changed, and why.
4. **Make sure to delete merged branches!**

### 🪶 Checking others' pull requests

1. You can view pull requests at https://github.com/kioszaha/data-wrangling/pulls.
2. Once on a pull request, switch to the `Files changed` tab to inspect all added or modified code.
3. Click the `+` icon next to ask questions, suggest improvements, or point out bugs.
4. Click `Review changes` and choose `Approve` or `Request changes`, then post your overall summary comment.
5. Message the chat to let the group know you provided feedback.

## 📦Packages

Use `uv` to manage packages

1. Download/install `uv` and ensure its CLI is operational
   - Windows: `winget install -e --id astral-sh.uv`
   - Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Run `uv sync` to sync your local packages with the repository's

Command cheat sheet:
|Command | Description |
|--|--|
| uv sync | Sync local packages with group's|
| uv add [package-name] | Install a new package |
| uv remove [package-name] | Remove a package |
| uv run [file-name].py| Run a file\*|

> \*Alternatively, you can activate the virtual environment (e.g, with `.venv/Scripts/activate`) and then run files like normal (e.g, `py [file-name].py`).

## 📊 Documentation

- [Airbnb dataset source, column meanings, and cleaning decisions](docs/airbnb.md)
- [Tenancy Services bond dataset source, column meanings, and cleaning decisions](docs/bonds.md)
- [Design principles: pipeline inputs, outputs, steps, and coding strategies](docs/design_principles.md)
- [Coding standards, changes made, and a worked sanity check](docs/coding_standards.md)

Run the complete reproducible pipeline with:

```text
uv run main.py
```

### Updating with new Airbnb months

`uv run main.py` is all that's needed to bring the results up to date:

1. Get the new `listings.csv` from [Inside Airbnb](https://insideairbnb.com/get-the-data/), not the `.csv.gz`.
   Don't open it in Excel, as that corrupts the IDs and dates.
2. Upload it to the team CDN (or save it in the airbnb data folder) named by snapshot date, for example `listings_20260813.csv`.
3. Run `uv run main.py`. New files are synced, every month found is combined, and the plots, cleaned datasets, joins and analysis answers are regenerated.

Re-runs are fast because area codes that were already looked up are cached. Only new coordinates are sent to the Koordinates API.

In order to run the entirety of deliverable 5, the KOORDINATES_API_KEY environment variable is required.

This can be obtained from [Koordinates](https://koordinates.com/my/api/) and added to your .env file (it will be automatically read).

   Deliverable 3 re-runs last week's R plots through `rpy2`, so those plots are only written when a
   working R installation is available. Without R that one step logs that it is skipping and the
   rest of the pipeline continues.
