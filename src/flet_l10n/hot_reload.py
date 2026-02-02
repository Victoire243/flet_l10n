"""Hot-reload support for ARB files during development."""

import logging
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class ARBFileHandler(FileSystemEventHandler):
    """File system event handler for ARB file changes."""

    def __init__(self, callback: Callable[[str], None]):
        """Initialize ARB file handler.

        Args:
            callback: Function to call when ARB files change
        """
        super().__init__()
        self.callback = callback

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith(".arb"):
            logger.info(f"ARB file modified: {event.src_path}")
            self.callback(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith(".arb"):
            logger.info(f"ARB file created: {event.src_path}")
            self.callback(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory and event.src_path.endswith(".arb"):
            logger.info(f"ARB file deleted: {event.src_path}")
            self.callback(event.src_path)


class HotReloadWatcher:
    """Watches ARB directory for changes and triggers reload."""

    def __init__(
        self, arb_dir: Path | str, on_change: Optional[Callable[[str], None]] = None
    ):
        """Initialize hot-reload watcher.

        Args:
            arb_dir: Directory containing ARB files to watch
            on_change: Optional callback function called when files change
        """
        self.arb_dir = Path(arb_dir)
        self.on_change = on_change
        self._observer: Optional[Observer] = None
        self._is_watching = False

    def start(self) -> None:
        """Start watching for file changes."""
        if self._is_watching:
            logger.warning("Hot-reload watcher is already running")
            return

        if not self.arb_dir.exists():
            logger.error(f"ARB directory does not exist: {self.arb_dir}")
            return

        # Create event handler
        event_handler = ARBFileHandler(self._handle_change)

        # Create and start observer
        self._observer = Observer()
        self._observer.schedule(event_handler, str(self.arb_dir), recursive=False)
        self._observer.start()

        self._is_watching = True
        logger.info(f"Hot-reload watching: {self.arb_dir}")

    def stop(self) -> None:
        """Stop watching for file changes."""
        if not self._is_watching or not self._observer:
            return

        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
        self._is_watching = False
        logger.info("Hot-reload watcher stopped")

    def _handle_change(self, file_path: str) -> None:
        """Handle file change event.

        Args:
            file_path: Path to the changed file
        """
        logger.debug(f"Handling change for: {file_path}")

        if self.on_change:
            try:
                self.on_change(file_path)
            except Exception as e:
                logger.error(f"Error in hot-reload callback: {e}", exc_info=True)

    @property
    def is_watching(self) -> bool:
        """Check if watcher is currently active."""
        return self._is_watching

    def __enter__(self) -> "HotReloadWatcher":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self._is_watching:
            self.stop()
