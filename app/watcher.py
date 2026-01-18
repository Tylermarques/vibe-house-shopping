"""File watcher for monitoring the import directory for new HTML files."""

import logging
import threading
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent

from .parser import HomeDataParser
from .database import add_home, home_exists, init_db

logger = logging.getLogger(__name__)


class HTMLFileHandler(FileSystemEventHandler):
    """Handler for processing HTML files dropped into the import directory."""

    def __init__(self, import_dir: Path):
        self.import_dir = import_dir
        self.parser = HomeDataParser()
        self.processing_lock = threading.Lock()

    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            self._process_file(Path(event.src_path))

    def on_moved(self, event):
        """Handle file move events (e.g., when files are moved into the directory)."""
        if isinstance(event, FileMovedEvent) and not event.is_directory:
            self._process_file(Path(event.dest_path))

    def _process_file(self, file_path: Path):
        """Process an HTML file."""
        if file_path.suffix.lower() not in [".html", ".htm"]:
            return

        with self.processing_lock:
            # Wait a moment for the file to be fully written
            # This sleep is inside the lock to prevent race conditions where
            # multiple files arriving in quick succession could be processed
            # simultaneously before the lock is acquired
            time.sleep(0.5)
            try:
                logger.info(f"Processing file: {file_path.name}")
                data = self.parser.parse_file(file_path)

                if data:
                    if home_exists(
                        data.get("address", ""),
                        data.get("source_file", ""),
                        data.get("mls_id"),
                    ):
                        logger.info(f"Home already exists in database: {data.get('address')} (MLS: {data.get('mls_id')})")
                        return

                    home = add_home(data)
                    logger.info(f"Added home to database: {data.get('address')} (ID: {home.id})")
                else:
                    logger.warning(f"Could not extract home data from: {file_path.name}")

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")


class ImportWatcher:
    """Watches the import directory for new HTML files."""

    def __init__(self, import_dir: Path):
        self.import_dir = import_dir
        self.import_dir.mkdir(exist_ok=True)
        self.observer = Observer()
        self.handler = HTMLFileHandler(import_dir)
        self._running = False

    def start(self):
        """Start watching the import directory."""
        if self._running:
            return

        init_db()  # Ensure database is initialized

        # Process any existing files first
        self._process_existing_files()

        # Start watching for new files
        self.observer.schedule(self.handler, str(self.import_dir), recursive=False)
        self.observer.start()
        self._running = True
        logger.info(f"Started watching import directory: {self.import_dir}")

    def stop(self):
        """Stop watching the import directory."""
        if not self._running:
            return

        self.observer.stop()
        self.observer.join()
        self._running = False
        logger.info("Stopped import directory watcher")

    def _process_existing_files(self):
        """Process any HTML files already in the import directory."""
        for file_path in self.import_dir.glob("*.html"):
            self.handler._process_file(file_path)
        for file_path in self.import_dir.glob("*.htm"):
            self.handler._process_file(file_path)

    @property
    def is_running(self):
        """Check if the watcher is running."""
        return self._running
