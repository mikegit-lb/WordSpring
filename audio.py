"""Asynchronous offline pronunciation rendering and local audio cache."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

logger = logging.getLogger(__name__)


class AudioManager(QObject):
    """Render a word once, cache it, then play it without blocking the UI."""

    audio_ready = Signal(str)
    message = Signal(str)

    def __init__(self, cache_dir: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.cache_dir = cache_dir
        self._cache_error = ""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as cache_exc:
            fallback = Path(tempfile.gettempdir()) / "WordSpring" / "audio"
            try:
                fallback.mkdir(parents=True, exist_ok=True)
                self.cache_dir = fallback
            except OSError as fallback_exc:
                self._cache_error = f"{cache_exc}; {fallback_exc}"
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="word-audio")
        self.audio_ready.connect(self._play_file)
        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
        self._player.errorOccurred.connect(self._on_playback_error)
        self._closed = False

    def speak(self, text: str) -> None:
        text = text.strip()
        if not text or self._closed:
            return
        if self._cache_error:
            self._emit_message(f"Ses dosyası için yazma alanı açılamadı: {self._cache_error}")
            return
        self.message.emit("Telaffuz hazırlanıyor…")
        try:
            self._executor.submit(self._prepare_audio, text)
        except RuntimeError:
            if not self._closed:
                raise

    @staticmethod
    def _cache_stem(text: str) -> str:
        return hashlib.sha256(text.casefold().encode("utf-8")).hexdigest()

    def _prepare_audio(self, text: str) -> None:
        stem = self._cache_stem(text)
        try:
            for suffix in (".wav", ".mp3"):
                cached = self.cache_dir / f"{stem}{suffix}"
                if cached.is_file() and cached.stat().st_size > 0:
                    self._emit_audio(str(cached))
                    return
        except OSError as exc:
            self._emit_message(f"Önbelleğe kaydedilmiş ses okunamadı: {exc}")
            return

        offline_error: Exception | None = None
        try:
            rendered = self._render_sapi(text, stem)
            self._emit_audio(str(rendered))
            return
        except Exception as exc:  # noqa: BLE001 -- SAPI and COM raise backend-specific exceptions.
            offline_error = exc
            # Try the optional online provider if SAPI/pyttsx3 is unavailable.
            logger.warning("Offline pronunciation synthesis failed: %s", exc)

        try:
            rendered = self._render_edge_tts(text, stem)
            self._emit_audio(str(rendered))
            self._emit_message("İsteğe bağlı çevrimiçi telaffuz kullanılıyor.")
        except ImportError as exc:
            self._emit_message(
                "İngilizce ses oluşturulamadı. Windows'ta İngilizce bir metin okuma sesi etkinleştirip "
                f"yeniden dene. Çevrimdışı ses: {offline_error}; çevrimiçi ses: {exc}"
            )
        except Exception as exc:
            logger.exception("Pronunciation synthesis failed")
            self._emit_message(
                "Telaffuz oluşturulamadı. Windows konuşma seslerini veya isteğe bağlı "
                f"edge-tts bağlantısını kontrol et. ({exc})"
            )

    def _emit_audio(self, path: str) -> None:
        if self._closed:
            return
        try:
            self.audio_ready.emit(path)
        except RuntimeError:
            # The window may have closed while the background synthesis was running.
            return

    def _emit_message(self, message: str) -> None:
        if self._closed:
            return
        try:
            self.message.emit(message)
        except RuntimeError:
            return

    def _render_sapi(self, text: str, stem: str) -> Path:
        import pyttsx3

        pythoncom = None
        if os.name == "nt":
            try:
                import pythoncom as win32_com  # type: ignore[import-not-found]
                pythoncom = win32_com
                pythoncom.CoInitialize()
            except ImportError:
                pythoncom = None
        destination = self.cache_dir / f"{stem}.wav"
        fd, temporary_name = tempfile.mkstemp(suffix=".wav", dir=self.cache_dir)
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            driver = "sapi5" if os.name == "nt" else None
            engine = pyttsx3.init(driverName=driver) if driver else pyttsx3.init()
            engine.setProperty("rate", 155)
            self._select_english_voice(engine)
            engine.save_to_file(text, str(temporary))
            engine.runAndWait()
            engine.stop()
            if not temporary.is_file() or temporary.stat().st_size < 44:
                raise RuntimeError("The speech engine returned an empty audio file.")
            os.replace(temporary, destination)
            return destination
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)
            if pythoncom is not None:
                pythoncom.CoUninitialize()

    @staticmethod
    def _select_english_voice(engine) -> None:
        """Prefer an installed English SAPI voice when Windows offers one."""
        try:
            voices = engine.getProperty("voices") or []
            descriptions: list[tuple[str, str]] = []
            for voice in voices:
                languages = getattr(voice, "languages", []) or []
                language_text = " ".join(
                    value.decode("utf-8", errors="ignore") if isinstance(value, bytes) else str(value)
                    for value in languages
                )
                label = f"{getattr(voice, 'id', '')} {getattr(voice, 'name', '')} {language_text}".casefold()
                if "english" in label or "en-us" in label or "en-gb" in label or "en_" in label:
                    descriptions.append((label, getattr(voice, "id", "")))
            if descriptions:
                descriptions.sort(key=lambda item: ("en-us" not in item[0] and "en_us" not in item[0], item[0]))
                engine.setProperty("voice", descriptions[0][1])
        except Exception:  # noqa: BLE001 -- Voice enumeration is optional; retain the default voice.
            # Use the operating system's default voice if enumeration is restricted.
            return

    def _render_edge_tts(self, text: str, stem: str) -> Path:
        import edge_tts  # type: ignore[import-not-found]

        destination = self.cache_dir / f"{stem}.mp3"
        fd, temporary_name = tempfile.mkstemp(suffix=".mp3", dir=self.cache_dir)
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            async def save() -> None:
                communicator = edge_tts.Communicate(text, "en-US-AriaNeural")
                await communicator.save(str(temporary))

            asyncio.run(save())
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise RuntimeError("The online speech service returned an empty audio file.")
            os.replace(temporary, destination)
            return destination
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)

    def _play_file(self, path: str) -> None:
        if self._closed:
            return
        self._player.stop()
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()

    def _on_playback_error(self, _error: QMediaPlayer.Error, error_string: str) -> None:
        if error_string:
            self.message.emit(f"Ses çalınamıyor: {error_string}")

    def close(self) -> None:
        self._closed = True
        self._player.stop()
        self._executor.shutdown(wait=False, cancel_futures=True)
