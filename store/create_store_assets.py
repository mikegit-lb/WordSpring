"""Create Store logos and real UI screenshots using the installed Qt runtime."""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QApplication

from database import Database
from ui_main import MainWindow

ASSET_DIR = Path(__file__).resolve().parent / "Assets"
SCREENSHOT_DIR = Path(__file__).resolve().parent / "Screenshots"
NAVY = QColor("#142640")
BLUE = QColor("#326bce")
WHITE = QColor("#f7f9ff")
CORAL = QColor("#ffb477")


def _draw_mark(painter: QPainter, rect: QRectF) -> None:
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    background = QLinearGradient(rect.topLeft(), rect.bottomRight())
    background.setColorAt(0, NAVY)
    background.setColorAt(1, BLUE)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(background)
    painter.drawRoundedRect(rect, w * 0.23, h * 0.23)

    left_page = QPainterPath(QPointF(x + w * 0.19, y + h * 0.34))
    left_page.cubicTo(x + w * 0.32, y + h * 0.30, x + w * 0.42, y + h * 0.36, x + w * 0.49, y + h * 0.44)
    left_page.lineTo(x + w * 0.49, y + h * 0.72)
    left_page.cubicTo(x + w * 0.39, y + h * 0.64, x + w * 0.28, y + h * 0.62, x + w * 0.18, y + h * 0.66)
    left_page.closeSubpath()
    right_page = QPainterPath(QPointF(x + w * 0.51, y + h * 0.44))
    right_page.cubicTo(x + w * 0.59, y + h * 0.36, x + w * 0.69, y + h * 0.30, x + w * 0.82, y + h * 0.34)
    right_page.lineTo(x + w * 0.82, y + h * 0.66)
    right_page.cubicTo(x + w * 0.72, y + h * 0.62, x + w * 0.61, y + h * 0.64, x + w * 0.51, y + h * 0.72)
    right_page.closeSubpath()
    painter.setBrush(WHITE)
    painter.drawPath(left_page)
    painter.drawPath(right_page)
    painter.setPen(QPen(CORAL, max(1.2, w * 0.025), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(x + w * 0.50, y + h * 0.45), QPointF(x + w * 0.50, y + h * 0.72))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(CORAL)
    painter.drawEllipse(QRectF(x + w * 0.68, y + h * 0.17, w * 0.09, h * 0.09))
    painter.restore()


def _create_icon(filename: str, width: int, height: int | None = None) -> None:
    height = height or width
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    if width == height:
        _draw_mark(painter, QRectF(0, 0, width, height))
    else:
        background = QLinearGradient(0, 0, width, height)
        background.setColorAt(0, NAVY)
        background.setColorAt(1, BLUE)
        painter.fillRect(QRectF(0, 0, width, height), background)
        mark_size = height * 0.77
        _draw_mark(painter, QRectF(height * 0.12, height * 0.115, mark_size, mark_size))
        painter.setPen(WHITE)
        painter.setFont(QFont("Segoe UI", max(10, int(height * 0.17)), QFont.Weight.Bold))
        painter.drawText(QRectF(height, 0, width - height - 6, height * 0.62), Qt.AlignmentFlag.AlignVCenter, "WordSpring")
        painter.setFont(QFont("Segoe UI", max(7, int(height * 0.07))))
        painter.drawText(QRectF(height + 2, height * 0.54, width - height - 8, height * 0.31), Qt.AlignmentFlag.AlignVCenter, "İngilizce kelime çalışması")
    painter.end()
    if not image.save(str(ASSET_DIR / filename), "PNG"):
        raise OSError(f"Could not save {filename}")


def create_logos() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for name, size in (
        ("StoreLogo.png", 50),
        ("Square44x44Logo.png", 44),
        ("Square71x71Logo.png", 71),
        ("Square150x150Logo.png", 150),
        ("Square310x310Logo.png", 310),
    ):
        _create_icon(name, size)
    _create_icon("Wide310x150Logo.png", 310, 150)
    _create_icon("SplashScreen.png", 620, 300)
    png_images: list[tuple[int, bytes]] = []
    for size in (256, 64, 48, 32, 16):
        image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        _draw_mark(painter, QRectF(0, 0, size, size))
        painter.end()
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        buffer.close()
        png_images.append((size, bytes(data)))
    offset = 6 + 16 * len(png_images)
    directory = bytearray()
    payload = bytearray()
    for size, data in png_images:
        dimension = 0 if size == 256 else size
        directory.extend(struct.pack("<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset))
        payload.extend(data)
        offset += len(data)
    icon = struct.pack("<HHH", 0, 1, len(png_images)) + directory + payload
    (ASSET_DIR / "WordSpring.ico").write_bytes(icon)


def create_screenshots(app: QApplication) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    for page_name, page_index, action in (
        ("01-study.png", 0, "flip"),
        ("02-practice.png", 1, "b1"),
        ("03-progress.png", 3, "none"),
    ):
        with TemporaryDirectory(prefix="wordspring-store-preview-") as temp_dir:
            db_path = Path(temp_dir) / "vocab.db"
            database = Database(db_path)
            window = MainWindow(database, Path(temp_dir) / "audio")
            try:
                window.theme = "light"
                window._apply_theme()
                window.resize(1366, 768)
                window.tabs.setCurrentIndex(page_index)
                if action == "flip":
                    window.study_page.flip()
                elif action == "b1":
                    window.quiz_page.mode.setCurrentIndex(1)
                window.show()
                app.processEvents()
                image = QImage(window.size(), QImage.Format.Format_ARGB32_Premultiplied)
                image.fill(QColor("#f4f6fb"))
                painter = QPainter(image)
                window.render(painter, QPoint(0, 0))
                painter.end()
                output = SCREENSHOT_DIR / page_name
                if not image.save(str(output), "PNG"):
                    raise OSError(f"Could not save {output}")
            finally:
                window.close()
                app.processEvents()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("WordSpring")
    app.setOrganizationName("WordSpring")
    app.setApplicationVersion("1.0.1")
    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    segoe_ui = windows_dir / "Fonts" / "segoeui.ttf"
    if segoe_ui.is_file():
        QFontDatabase.addApplicationFont(str(segoe_ui))
    app.setFont(QFont("Segoe UI", 10))
    create_logos()
    create_screenshots(app)
    print(f"Created Store logos in {ASSET_DIR}")
    print(f"Created Store listing screenshots in {SCREENSHOT_DIR}")


if __name__ == "__main__":
    main()
