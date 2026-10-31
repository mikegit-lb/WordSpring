"""WordSpring desktop vocabulary learner entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database import Database, default_database_path
from ui_main import MainWindow, show_startup_error

APP_VERSION = "1.0.1"


def audio_cache_path(database_path: Path) -> Path:
    return database_path.parent / "audio"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("WordSpring")
    app.setOrganizationName("WordSpring")
    app.setApplicationDisplayName("WordSpring İngilizce Kelime Öğrenme")
    app.setApplicationVersion(APP_VERSION)
    db_path = default_database_path()
    database: Database | None = None
    try:
        database = Database(db_path)
        window = MainWindow(database, audio_cache_path(db_path), database.recovered_from_corruption)
    except Exception as exc:  # noqa: BLE001 -- Show an actionable dialog for any startup failure.
        if database is not None:
            database.close()
        show_startup_error(exc)
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
