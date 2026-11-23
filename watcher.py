from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sorter_engine import DownSortEngine, PARTIAL_EXTENSIONS


class DownloadEventHandler(FileSystemEventHandler):
    def __init__(self, engine: DownSortEngine):
        super().__init__()
        self.engine = engine
        self.is_paused = False

    def on_created(self, event):
        if self.is_paused or event.is_directory:
            return
        self.engine.process_file(Path(event.src_path))

    def on_modified(self, event):
        if self.is_paused or event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix.lower() in PARTIAL_EXTENSIONS:
            self.engine.process_file(file_path)

    def on_moved(self, event):
        if self.is_paused or event.is_directory:
            return
        self.engine.on_download_complete(Path(event.src_path), Path(event.dest_path))


class DownSortWatcher:
    def __init__(self, engine: DownSortEngine):
        self.engine = engine
        self.handler = DownloadEventHandler(engine)
        self.observer = None

    def start(self):
        if self.observer and self.observer.is_alive():
            return
        self.engine.scan_existing_files()
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.engine.downloads_dir), recursive=False)
        self.observer.daemon = True
        self.observer.start()
        self.engine.emit_log("WATCHER", "Live file-system monitor active.")

    def stop(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            self.engine.emit_log("WATCHER", "Live monitor stopped.")

    def set_paused(self, paused: bool):
        self.handler.is_paused = paused
        state = "SUSPENDED" if paused else "ACTIVE"
        self.engine.emit_log("SYSTEM", f"Monitoring state: {state}")