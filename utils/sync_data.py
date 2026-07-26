"""
Check if there is any data that is not replicated locally, and replicate it.
"""

import hashlib
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table

from config import DATA_DIR

DATA_URL = "https://data-wrangling-cdn.oskar.nz"
console = Console()


def calculate_md5(file_path: Path) -> str:
    """Calculate the hex MD5 hash of a local file in 64KB chunks."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5.update(chunk)
    return md5.hexdigest()


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """Ensure target path remains inside base_dir to prevent path traversal."""
    try:
        return target_path.resolve().is_relative_to(base_dir.resolve())
    except (ValueError, RuntimeError):
        return False


def build_status_table(missing_files: list[dict]) -> Table:
    """Util function download status table"""
    table = Table(box=None)
    table.add_column("Status")
    table.add_column("File")
    table.add_column("Size", justify="right")
    table.add_column("Progress", justify="right")

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

    for file in missing_files:
        status = file["status"]
        color = color_key[status]
        total_bytes = file.get("size", 0)
        size_mb = total_bytes / (1024**2)

        pct = (
            (file.get("downloaded", 0) / total_bytes * 100) if total_bytes > 0 else 0.0
        )
        progress_str = f"{pct:.1f}%"

        table.add_row(
            f"[{color}]{emoji_key[status]}[/{color}]",
            f"[{color}]{file['key']}[/{color}]",
            f"[{color}]{size_mb:.2f} MB[/{color}]",
            f"[{color}]{progress_str}[/{color}]",
        )

    return table


def sync_data() -> None:
    """Check missing remote files and safely replicate them locally."""
    api_url = urljoin(DATA_URL, "/api/files")

    try:
        res = requests.get(api_url, timeout=10)
        res.raise_for_status()
        data = res.json()
    except (requests.exceptions.RequestException, ValueError):
        console.print(
            "[bold red]⚠️ Unable to sync files due to network error or malformed response[/bold red]"
        )
        return

    file_list = data.get("files")
    if not isinstance(file_list, list):
        console.print(
            "[bold red]⚠️ Unable to sync files due malformed response[/bold red]"
        )
        return

    missing_files = []
    base_dir = DATA_DIR.resolve()

    for file_info in file_list:
        key = file_info.get("key", "").lstrip("/")
        remote_etag = file_info.get("etag", "").strip('"')
        file_path = (DATA_DIR / key).resolve()

        if not is_safe_path(base_dir, file_path):
            console.print(f"[bold red]⚠️ Skipping funky key path: {key}[/bold red]")
            continue

        if not file_path.exists():
            console.print(f"[bold yellow]Missing:[bold yellow] {key}")
        elif calculate_md5(file_path) != remote_etag:
            console.print(f"[bold yellow]Modified:[bold yellow] {key}")
        else:
            continue

        file_info["path"] = file_path
        file_info["status"] = "pending"
        file_info["downloaded"] = 0
        missing_files.append(file_info)

    local_flag = False
    all_paths = {Path(file["key"]) for file in file_list}
    for file in DATA_DIR.rglob("*"):
        if not file.is_file():
            continue
        local_path = file.relative_to(DATA_DIR)
        if local_path not in all_paths:
            if os.environ.get("DELETE_UNKNOWN_FILES") == "TRUE":
                file.unlink()
                continue
            console.print(
                f"[bold yellow]{local_path} is present locally but not remotely[/bold yellow]"
            )
            local_flag = True

    if local_flag:
        console.print(
            "[italic yellow]To auto delete local files that are not present remotely, set the DELETE_UNKNOWN_FILES environment variable to TRUE[/italic yellow]"
        )

    if not missing_files:
        console.print("[bold green]✅ Local data files are up to date[/bold green]")
        return

    with Live(
        build_status_table(missing_files), console=console, refresh_per_second=10
    ) as live:
        for file_info in missing_files:
            file_info["status"] = "downloading"
            live.update(build_status_table(missing_files))

            target_path: Path = file_info["path"]
            temp_path = target_path.with_name(target_path.name + ".tmp")
            file_url = urljoin(DATA_URL, f"/files/{file_info['key']}")

            try:
                res = requests.get(file_url, stream=True, timeout=30)
                res.raise_for_status()

                target_path.parent.mkdir(parents=True, exist_ok=True)

                last_ui_update = time.time()
                with open(temp_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            file_info["downloaded"] += len(chunk)

                            if time.time() - last_ui_update > 0.1:
                                live.update(build_status_table(missing_files))
                                last_ui_update = time.time()

                temp_path.replace(target_path)
                file_info["status"] = "completed"

            except (requests.exceptions.RequestException, OSError):
                file_info["status"] = "failed"
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)

            live.update(build_status_table(missing_files))
