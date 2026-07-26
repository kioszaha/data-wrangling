"""
Check if there is any data that is not replicated locally, and replicate it.
"""

from pathlib import Path

import requests
from rich.live import Live

from config import DATA_DIR

DATA_URL = "https://data-wrangling-cdn.oskar.nz"


def sync_data() -> None:
    """
    Check if there is any data that is not replicated locally, and replicate it.
    """

    with Live() as live:
        live.update("[bold blue]⌛ Checking remote files...[/bold blue]")

        # Request a list of files from the server
        try:
            res = requests.get(DATA_URL + "/api/files")
            files = res.json()
        except requests.exceptions.RequestException:
            live.update(
                "[bold red]⚠️ Unable to sync files due to network error. The code may not work properly if there are missing files.[/bold red]"
            )
            return

        # Make sure the files follow a structure we expect
        if "files" not in files or not isinstance(files["files"], list):
            live.update(
                "[bold red]⚠️ Unable to sync files due to malformed response. The code may not work properly if there are missing files.[/bold red]"
            )
            return

        # Loop through each file returned, and check if it's there.
        missing_files = []
        files = files["files"]
        for file in files:
            file_path: Path = DATA_DIR / file["key"]
            if not file_path.exists():
                file["path"] = file_path
                file["status"] = "pending"
                file["downloaded"] = 0
                missing_files.append(file)

        # Check if we have files to download
        if len(missing_files) == 0:
            live.update("[bold green]✅ Local data files are up to date[/bold green]")
            return

        # Helper function to update print state
        def reflect_state() -> None:
            emoji_key = {
                "pending": "⌛",
                "downloading": "⬇️ ",
                "completed": "✅",
                "failed": "❌",
            }
            color_key = {
                "pending": "grey84",
                "downloading": "blue",
                "completed": "green",
                "failed": "red",
            }
            file_rows = []
            for file in missing_files:
                status = file["status"]
                total_bytes = file.get("size", 0)
                size_mb = total_bytes / 1024**2

                # Calculate percentage if actively downloading and total size is known
                progress_str = ""
                if status == "downloading" and total_bytes > 0:
                    pct = (file.get("downloaded", 0) / total_bytes) * 100
                    progress_str = f"{pct:.2f}%"

                file_rows.append(
                    f"[{color_key[status]}]{emoji_key[status]} {file['key']} ({size_mb:.2f}mb) {progress_str}[/{color_key[status]}]"
                )
            live.update(
                "[bold underline blue]Syncing files...[/bold underline blue]\n"
                + "\n".join(file_rows)
            )

        # Loop through files and download them
        for file in missing_files:
            file["status"] = "downloading"
            reflect_state()
            try:
                res = requests.get(
                    DATA_URL + "/files/" + file["key"], stream=True, timeout=30
                )
                res.raise_for_status()

                file["path"].parent.mkdir(parents=True, exist_ok=True)
                with open(file["path"], "wb") as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            file["downloaded"] += len(chunk)
                            reflect_state()
                file["status"] = "completed"

            except requests.exceptions.RequestException:
                file["status"] = "failed"

            reflect_state()
