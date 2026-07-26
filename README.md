# Team KIOSZAHA : Data Wrangling

## 🥸 Team members:

- 🙀 Oskar Greig

- � Zaeim Imran Bin Mohd Nazri

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
