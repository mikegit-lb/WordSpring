"""SQLite persistence, schema migrations, seed loading, and progress queries."""

from __future__ import annotations

import os
import shutil
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from seed_data import get_seed_words
from srs import Rating, ReviewState, schedule_review

APP_DIRECTORY = "WordSpring"
SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class Word:
    id: int
    word: str
    cefr_level: str
    part_of_speech: str
    definition: str
    example_sentence: str
    collocations: str
    ease_factor: float
    interval: float
    repetitions: int
    next_review: str
    phonetics: str = ""


def default_database_path() -> Path:
    """Return a writable per-user database path that also works in a one-file exe."""
    root = os.environ.get("LOCALAPPDATA")
    if root:
        base = Path(root)
    else:
        base = Path.home() / ".local" / "share"
    return base / APP_DIRECTORY / "vocab.db"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class DatabaseError(RuntimeError):
    """Actionable database initialization or persistence error."""


class Database:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: sqlite3.Connection | None = None
        self.recovered_from_corruption = False
        self._open_with_recovery()
        self._migrate()
        self.seed_if_empty()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _open_with_recovery(self) -> None:
        try:
            self._connection = self._connect()
            result = self._connection.execute("PRAGMA quick_check").fetchone()
            if result and result[0] != "ok":
                raise sqlite3.DatabaseError(f"integrity check failed: {result[0]}")
        except sqlite3.DatabaseError as exc:
            if self._connection is not None:
                self._connection.close()
                self._connection = None
            if not self.path.exists() or self.path.stat().st_size == 0:
                raise DatabaseError(f"Kelime veritabanı açılamadı: {exc}") from exc
            message = str(exc).casefold()
            damaged = any(
                marker in message
                for marker in ("malformed", "not a database", "integrity check failed", "disk image")
            )
            if not damaged:
                raise DatabaseError(f"Kelime veritabanı açılamadı: {exc}") from exc
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            backup_path = self.path.with_name(f"vocab.corrupt-{stamp}.db")
            try:
                shutil.move(str(self.path), str(backup_path))
                for suffix in ("-wal", "-shm"):
                    sidecar = Path(str(self.path) + suffix)
                    if sidecar.exists():
                        shutil.move(str(sidecar), str(backup_path) + suffix)
                self._connection = self._connect()
                self.recovered_from_corruption = True
            except (OSError, sqlite3.DatabaseError) as recovery_exc:
                raise DatabaseError(
                    "Kelime veritabanı hasarlı ve kurtarılamadı. "
                    f"Özgün dosya: {self.path}. Ayrıntı: {recovery_exc}"
                ) from recovery_exc

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise DatabaseError("Kelime veritabanı açık değil.")
        return self._connection

    def _migrate(self) -> None:
        connection = self.connection
        try:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise DatabaseError(
                    "Bu veritabanı WordSpring'in daha yeni bir sürümüyle oluşturulmuş. "
                    "Kullanmak için uygulamayı güncelle."
                )
            with connection:
                if version < 1:
                    connection.execute(
                        """CREATE TABLE IF NOT EXISTS words (
                            id INTEGER PRIMARY KEY,
                            word TEXT NOT NULL UNIQUE,
                            cefr_level TEXT NOT NULL CHECK (cefr_level IN ('A2', 'B1')),
                            part_of_speech TEXT NOT NULL,
                            definition TEXT NOT NULL,
                            example_sentence TEXT NOT NULL,
                            collocations TEXT NOT NULL DEFAULT '',
                            ease_factor REAL NOT NULL DEFAULT 2.5,
                            interval REAL NOT NULL DEFAULT 0,
                            repetitions INTEGER NOT NULL DEFAULT 0,
                            next_review TEXT NOT NULL
                        )"""
                    )
                    connection.execute("PRAGMA user_version = 1")
                    version = 1
                if version < 2:
                    columns = {
                        row[1] for row in connection.execute("PRAGMA table_info(words)")
                    }
                    if "phonetics" not in columns:
                        connection.execute(
                            "ALTER TABLE words ADD COLUMN phonetics TEXT NOT NULL DEFAULT ''"
                        )
                    if "created_at" not in columns:
                        connection.execute(
                            "ALTER TABLE words ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"
                        )
                    connection.execute(
                        """CREATE TABLE IF NOT EXISTS review_events (
                            id INTEGER PRIMARY KEY,
                            word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
                            reviewed_at TEXT NOT NULL,
                            local_date TEXT NOT NULL,
                            mode TEXT NOT NULL,
                            quality INTEGER NOT NULL CHECK (quality BETWEEN 0 AND 5),
                            was_correct INTEGER NOT NULL CHECK (was_correct IN (0, 1))
                        )"""
                    )
                    connection.execute(
                        "CREATE INDEX IF NOT EXISTS idx_words_due ON words(next_review, cefr_level)"
                    )
                    connection.execute(
                        "CREATE INDEX IF NOT EXISTS idx_events_date ON review_events(local_date, reviewed_at)"
                    )
                    connection.execute("PRAGMA user_version = 2")
        except (sqlite3.DatabaseError, OSError) as exc:
            if isinstance(exc, DatabaseError):
                raise
            raise DatabaseError(f"Kelime veritabanı güncellenemedi: {exc}") from exc

    def seed_if_empty(self) -> None:
        """Insert starter vocabulary idempotently, preserving existing study data."""
        connection = self.connection
        now = utc_now_iso()
        try:
            with connection:
                for item in get_seed_words():
                    connection.execute(
                        """INSERT OR IGNORE INTO words
                           (word, cefr_level, part_of_speech, definition, example_sentence,
                            collocations, ease_factor, interval, repetitions, next_review,
                            phonetics, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, 2.5, 0, 0, ?, ?, ?)""",
                        (
                            item["word"], item["cefr_level"], item["part_of_speech"],
                            item["definition"], item["example_sentence"],
                            item["collocations"], now, item["phonetics"], now,
                        ),
                    )
        except sqlite3.DatabaseError as exc:
            raise DatabaseError(f"Başlangıç kelimeleri yüklenemedi: {exc}") from exc

    @staticmethod
    def _word(row: sqlite3.Row) -> Word:
        return Word(
            id=row["id"], word=row["word"], cefr_level=row["cefr_level"],
            part_of_speech=row["part_of_speech"], definition=row["definition"],
            example_sentence=row["example_sentence"], collocations=row["collocations"],
            ease_factor=row["ease_factor"], interval=row["interval"],
            repetitions=row["repetitions"], next_review=row["next_review"],
            phonetics=row["phonetics"],
        )

    @staticmethod
    def _level_clause(level: str | None) -> tuple[str, tuple[Any, ...]]:
        if level in ("A2", "B1"):
            return " WHERE cefr_level = ?", (level,)
        return "", ()

    def count_words(self, level: str | None = None) -> int:
        clause, params = self._level_clause(level)
        return int(self.connection.execute(f"SELECT COUNT(*) FROM words{clause}", params).fetchone()[0])

    def count_due_words(self, level: str | None = None) -> int:
        clause, params = self._level_clause(level)
        joiner = " AND " if clause else " WHERE "
        row = self.connection.execute(
            f"SELECT COUNT(*) FROM words{clause}{joiner}next_review <= ?",
            params + (utc_now_iso(),),
        ).fetchone()
        return int(row[0] or 0)

    def get_due_words(
        self,
        level: str | None = None,
        exclude_ids: Iterable[int] = (),
    ) -> list[Word]:
        clause, params = self._level_clause(level)
        query = "SELECT * FROM words" + clause
        if clause:
            query += " AND next_review <= ?"
        else:
            query += " WHERE next_review <= ?"
        values: tuple[Any, ...] = params + (utc_now_iso(),)
        excluded = tuple({int(value) for value in exclude_ids})
        if excluded:
            query += f" AND id NOT IN ({','.join('?' for _ in excluded)})"
            values += excluded
        query += " ORDER BY next_review, lower(word) LIMIT 1"
        row = self.connection.execute(query, values).fetchone()
        return [self._word(row)] if row else []

    def get_random_words(self, level: str | None = None, limit: int = 4) -> list[Word]:
        clause, params = self._level_clause(level)
        rows = self.connection.execute(
            f"SELECT * FROM words{clause} ORDER BY RANDOM() LIMIT ?", params + (limit,)
        ).fetchall()
        return [self._word(row) for row in rows]

    def get_random_b1_words(self, limit: int = 4) -> list[Word]:
        rows = self.connection.execute(
            "SELECT * FROM words WHERE cefr_level = 'B1' ORDER BY RANDOM() LIMIT ?", (limit,)
        ).fetchall()
        return [self._word(row) for row in rows]

    def list_words(self, level: str | None = None, search: str = "") -> list[Word]:
        clause, params = self._level_clause(level)
        query = "SELECT * FROM words" + clause
        values: tuple[Any, ...] = params
        if search.strip():
            joiner = " AND " if clause else " WHERE "
            query += joiner + "(word LIKE ? OR definition LIKE ? OR part_of_speech LIKE ?)"
            term = f"%{search.strip()}%"
            values += (term, term, term)
        query += " ORDER BY cefr_level, lower(word)"
        rows = self.connection.execute(query, values).fetchall()
        return [self._word(row) for row in rows]

    def get_word(self, word_id: int) -> Word | None:
        row = self.connection.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        return self._word(row) if row else None

    def add_word(
        self,
        *,
        word: str,
        cefr_level: str,
        part_of_speech: str,
        definition: str,
        example_sentence: str,
        collocations: str = "",
        phonetics: str = "",
    ) -> int:
        values = {
            "word": word.strip(), "cefr_level": cefr_level.strip().upper(),
            "part_of_speech": part_of_speech.strip(), "definition": definition.strip(),
            "example_sentence": example_sentence.strip(), "collocations": collocations.strip(),
            "phonetics": phonetics.strip(),
        }
        if not values["word"] or values["cefr_level"] not in {"A2", "B1"}:
            raise ValueError("Bir kelime yaz ve A2 veya B1 seviyesini seç.")
        for field in ("part_of_speech", "definition", "example_sentence"):
            if not values[field]:
                raise ValueError("Sözcük türü, tanım ve örnek cümle gerekli.")
        duplicate = self.connection.execute(
            "SELECT 1 FROM words WHERE lower(word) = lower(?)", (values["word"],)
        ).fetchone()
        if duplicate:
            raise ValueError(f"‘{values['word']}’ zaten kelime listende var.")
        now = utc_now_iso()
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """INSERT INTO words
                       (word, cefr_level, part_of_speech, definition, example_sentence,
                        collocations, ease_factor, interval, repetitions, next_review,
                        phonetics, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, 2.5, 0, 0, ?, ?, ?)""",
                    (
                        values["word"], values["cefr_level"], values["part_of_speech"],
                        values["definition"], values["example_sentence"], values["collocations"],
                        now, values["phonetics"], now,
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("Bu kelime zaten listende var.") from exc
        except sqlite3.DatabaseError as exc:
            raise DatabaseError(f"Kelime kaydedilemedi: {exc}") from exc

    def review_word(self, word_id: int, rating: Rating | str, mode: str = "flashcard") -> None:
        rating = Rating(rating)
        row = self.connection.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        if row is None:
            raise DatabaseError("Bu kelime artık veritabanında yok.")
        state = ReviewState(row["ease_factor"], row["interval"], row["repetitions"])
        schedule = schedule_review(state, rating)
        quality = {Rating.AGAIN: 2, Rating.HARD: 3, Rating.GOOD: 4, Rating.EASY: 5}[rating]
        self._record_review(
            word_id=word_id, mode=mode, quality=quality,
            was_correct=rating is not Rating.AGAIN,
            update=(schedule.ease_factor, schedule.interval, schedule.repetitions, schedule.next_review),
        )

    def record_practice(self, word_id: int, correct: bool, mode: str) -> None:
        self._record_review(
            word_id=word_id, mode=mode, quality=4 if correct else 0,
            was_correct=correct, update=None,
        )

    def _record_review(
        self,
        *,
        word_id: int,
        mode: str,
        quality: int,
        was_correct: bool,
        update: tuple[float, float, int, str] | None,
    ) -> None:
        now = datetime.now().astimezone()
        try:
            with self.connection:
                self.connection.execute(
                    """INSERT INTO review_events
                       (word_id, reviewed_at, local_date, mode, quality, was_correct)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (word_id, now.astimezone(UTC).isoformat(timespec="seconds"),
                     now.date().isoformat(), mode, quality, int(was_correct)),
                )
                if update:
                    self.connection.execute(
                        """UPDATE words SET ease_factor = ?, interval = ?, repetitions = ?,
                           next_review = ? WHERE id = ?""",
                        (*update, word_id),
                    )
        except sqlite3.DatabaseError as exc:
            raise DatabaseError(f"Çalışma ilerlemen kaydedilemedi: {exc}") from exc

    def mastery_for(self, word: Word) -> str:
        if word.repetitions <= 0:
            return "New"
        if word.repetitions == 1:
            return "Learning"
        return "Learned"

    def dashboard(self) -> dict[str, int | float]:
        today = datetime.now().astimezone().date()
        row = self.connection.execute(
            """SELECT COUNT(*) AS total,
                      SUM(CASE WHEN repetitions >= 2 THEN 1 ELSE 0 END) AS learned,
                      SUM(CASE WHEN next_review <= ? THEN 1 ELSE 0 END) AS due
               FROM words""",
            (utc_now_iso(),),
        ).fetchone()
        accuracy_row = self.connection.execute(
            "SELECT AVG(was_correct) FROM (SELECT was_correct FROM review_events ORDER BY id DESC LIMIT 100)"
        ).fetchone()
        dates = [
            row[0] for row in self.connection.execute(
                "SELECT DISTINCT local_date FROM review_events ORDER BY local_date DESC LIMIT 400"
            ).fetchall()
        ]
        streak = 0
        expected = today
        if dates:
            latest = datetime.strptime(dates[0], "%Y-%m-%d").date()
            if latest == today or latest == today - timedelta(days=1):
                expected = latest
                for date_text in dates:
                    current = datetime.strptime(date_text, "%Y-%m-%d").date()
                    if current != expected:
                        break
                    streak += 1
                    expected -= timedelta(days=1)
        accuracy = float(accuracy_row[0] or 0.0) * 100.0
        return {
            "total": int(row["total"] or 0), "learned": int(row["learned"] or 0),
            "due": int(row["due"] or 0), "accuracy": round(accuracy), "streak": streak,
        }

    def level_progress(self) -> dict[str, dict[str, int]]:
        progress: dict[str, dict[str, int]] = {}
        for level in ("A2", "B1"):
            rows = self.connection.execute(
                """SELECT COUNT(*) AS total,
                          SUM(CASE WHEN repetitions = 0 THEN 1 ELSE 0 END) AS new,
                          SUM(CASE WHEN repetitions = 1 THEN 1 ELSE 0 END) AS learning,
                          SUM(CASE WHEN repetitions >= 2 THEN 1 ELSE 0 END) AS learned
                   FROM words WHERE cefr_level = ?""", (level,)
            ).fetchone()
            progress[level] = {key: int(rows[key] or 0) for key in ("total", "new", "learning", "learned")}
        return progress

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
