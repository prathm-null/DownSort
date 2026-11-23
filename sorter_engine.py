import time
import shutil
from pathlib import Path

# Temporary extensions created by browsers while downloading
PARTIAL_EXTENSIONS = {".crdownload", ".part", ".tmp", ".download"}
STAGING_FOLDER_NAME = "_In_Progress_Copies"


def get_unique_destination(target_folder: Path, filename: str) -> Path:
    """Prevents overwriting files with the same name by appending _1, _2, etc."""
    destination = target_folder / filename
    if not destination.exists():
        return destination

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1

    while True:
        candidate = target_folder / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


class DownSortEngine:
    def __init__(self, target_dir: Path = None, log_callback=None):
        self.downloads_dir = Path(target_dir) if target_dir else (Path.home() / "Downloads")
        self.staging_dir = self.downloads_dir / STAGING_FOLDER_NAME
        self.log_callback = log_callback

        # Telemetry counters for the UI
        self.sorted_count = 0
        self.staged_count = 0

    def emit_log(self, tag: str, message: str):
        formatted = f"[{tag}] {message}"
        print(formatted)
        if self.log_callback:
            self.log_callback(tag, message)

    def process_file(self, file_path: Path):
        """Decides whether to stage a partial file or sort a completed file."""
        file_path = Path(file_path)

        # 1. Ignore missing items, directories, or files inside the staging folder
        if not file_path.exists() or file_path.is_dir():
            return
        if self.staging_dir in file_path.parents:
            return

        ext = file_path.suffix.lower()

        # 2. CASE A: Half-downloaded / temporary file
        if ext in PARTIAL_EXTENSIONS:
            try:
                self.staging_dir.mkdir(parents=True, exist_ok=True)
                staged_copy = self.staging_dir / file_path.name
                shutil.copy2(file_path, staged_copy)
                self.staged_count += 1
                self.emit_log("STAGING", f"Copied partial file -> {STAGING_FOLDER_NAME}/{file_path.name}")
            except PermissionError:
                # Browser momentarily locked the chunk while writing; next event will catch it
                pass
            except Exception as e:
                self.emit_log("ERROR", f"Staging failed for {file_path.name}: {e}")
            return

        # 3. CASE B: Completed file -> Sort into dynamic extension folder
        # Brief pause so OS/browser releases file handle after creation/rename
        time.sleep(0.4)
        if not file_path.exists():
            return

        folder_name = ext[1:].upper() if ext else "NO_EXTENSION"
        dest_folder = self.downloads_dir / folder_name

        try:
            dest_folder.mkdir(parents=True, exist_ok=True)
            final_dest = get_unique_destination(dest_folder, file_path.name)
            shutil.move(str(file_path), str(final_dest))
            self.sorted_count += 1
            self.emit_log("SORTED", f"{file_path.name} -> /{folder_name}/{final_dest.name}")
        except PermissionError:
            self.emit_log("LOCKED", f"File in use, skipping for now: {file_path.name}")
        except Exception as e:
            self.emit_log("ERROR", f"Could not move {file_path.name}: {e}")

    def on_download_complete(self, old_path: Path, new_path: Path):
        """Called when a browser renames a partial download to its final filename."""
        old_path = Path(old_path)
        new_path = Path(new_path)

        # 1. Remove the staged partial copy if the old file was a partial download
        if old_path.suffix.lower() in PARTIAL_EXTENSIONS:
            staged_copy = self.staging_dir / old_path.name
            if staged_copy.exists():
                try:
                    staged_copy.unlink()
                    self.emit_log("CLEANUP", f"Deleted partial copy: {old_path.name}")
                except Exception as e:
                    self.emit_log("ERROR", f"Cleanup failed for {old_path.name}: {e}")

        # 2. Sort the newly completed file into its extension folder
        self.process_file(new_path)

    def scan_existing_files(self):
        """Scans root of Downloads folder for any unsorted files on startup."""
        self.emit_log("SYSTEM", f"Scanning {self.downloads_dir}...")
        for item in self.downloads_dir.iterdir():
            if item.is_file():
                self.process_file(item)
        self.emit_log("SYSTEM", "Initial scan complete.")