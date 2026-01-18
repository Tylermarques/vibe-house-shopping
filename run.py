#!/usr/bin/env python3
"""Main entry point for the Vibe House Shopping application."""

import logging
import signal
import sys
from pathlib import Path
from types import FrameType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.dash_app import create_app
from app.database import init_db
from app.watcher import ImportWatcher


def main() -> None:
    """Run the Vibe House Shopping application."""
    logger.info("Starting Vibe House Shopping...")

    # Initialize the database
    init_db()
    logger.info("Database initialized")

    # Set up the import directory watcher
    import_dir = PROJECT_ROOT / "import"
    watcher = ImportWatcher(import_dir)
    watcher.start()

    # Create and configure the Dash app
    app = create_app()

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum: int, frame: FrameType | None) -> None:
        logger.info("Shutting down...")
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the app
    logger.info("Starting Dash server at http://localhost:8050")
    logger.info(f"Drop HTML files into: {import_dir}")

    try:
        app.run(debug=True, host="0.0.0.0", port=8050)
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()
