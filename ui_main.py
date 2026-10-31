"""PySide6 user interface for the WordSpring vocabulary learner."""

from __future__ import annotations

import html
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from audio import AudioManager
from database import Database, DatabaseError, Word
from srs import Rating

LIGHT_QSS = """
QWidget { background: #f4f6fb; color: #1e293b; font-family: 'Segoe UI'; font-size: 10pt; }
QLabel { background: transparent; }
QMainWindow { background: #f4f6fb; }
QLabel#appTitle { color: #13223a; font-size: 25pt; font-weight: 700; }
QLabel#subtitle { color: #62718a; font-size: 10pt; }
QLabel#sectionTitle { color: #13223a; font-size: 18pt; font-weight: 700; }
QLabel#eyebrow { color: #71819a; font-size: 9pt; font-weight: 600; }
QLabel#wordTitle { color: #152944; font-size: 35pt; font-weight: 700; }
QLabel#definition { color: #33445e; font-size: 16pt; font-weight: 500; }
QLabel#metricValue { color: #152944; font-size: 24pt; font-weight: 700; }
QLabel#metricCaption { color: #71819a; font-size: 9pt; font-weight: 600; }
QLabel#feedback { min-height: 42px; font-size: 11pt; font-weight: 600; }
QFrame#metricCard, QFrame#studyCard, QFrame#surface, QFrame#levelCard {
    background: #ffffff; border: 1px solid #e4e9f2; border-radius: 16px;
}
QFrame#metricCard { min-height: 92px; }
QFrame#studyCard { min-height: 345px; }
QFrame#levelCard { min-height: 190px; }
QPushButton { background: #edf2f8; color: #283a54; border: 1px solid #dce4ef;
    border-radius: 10px; padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #e1eaf5; }
QPushButton:pressed { background: #d7e3f2; }
QPushButton:disabled { color: #91a0b3; background: #f4f6f9; }
QPushButton#primaryButton { background: #3069d9; color: #ffffff; border: 0; }
QPushButton#primaryButton:hover { background: #245cc9; }
QPushButton#goodButton { background: #e8f7ef; color: #177245; border-color: #c6ecd5; }
QPushButton#againButton { background: #fff0ee; color: #b33e34; border-color: #f6d3cf; }
QPushButton#hardButton { background: #fff6e8; color: #9a6415; border-color: #f0e0bf; }
QPushButton#easyButton { background: #eaf1ff; color: #2b57a6; border-color: #cfddfb; }
QLineEdit, QComboBox { background: #ffffff; color: #24354d; border: 1px solid #dbe3ee;
    border-radius: 9px; padding: 9px 11px; selection-background-color: #b8cef9; }
QComboBox QAbstractItemView { background: #ffffff; selection-background-color: #e8effc; }
QTabWidget::pane { border: 0; top: -1px; }
QTabBar::tab { background: transparent; color: #71819a; padding: 12px 17px;
    border-bottom: 2px solid transparent; font-weight: 600; }
QTabBar::tab:selected { color: #3069d9; border-bottom: 2px solid #3069d9; }
QTableWidget { background: #ffffff; alternate-background-color: #f8faff; gridline-color: #edf0f5;
    border: 1px solid #e2e8f1; border-radius: 10px; selection-background-color: #e6efff; }
QHeaderView::section { background: #f4f7fb; color: #697a92; border: 0;
    border-bottom: 1px solid #e4e9f2; padding: 10px; font-weight: 600; }
QProgressBar { background: #e8edf5; border: 0; border-radius: 6px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #4a7be0; border-radius: 6px; }
QStatusBar { color: #64748b; }
"""

DARK_QSS = """
QWidget { background: #121a27; color: #e6edf7; font-family: 'Segoe UI'; font-size: 10pt; }
QLabel { background: transparent; }
QMainWindow { background: #121a27; }
QLabel#appTitle { color: #f1f5fb; font-size: 25pt; font-weight: 700; }
QLabel#subtitle { color: #9cacbf; font-size: 10pt; }
QLabel#sectionTitle { color: #f1f5fb; font-size: 18pt; font-weight: 700; }
QLabel#eyebrow { color: #9cacbf; font-size: 9pt; font-weight: 600; }
QLabel#wordTitle { color: #f3f7ff; font-size: 35pt; font-weight: 700; }
QLabel#definition { color: #d5dfed; font-size: 16pt; font-weight: 500; }
QLabel#metricValue { color: #f3f7ff; font-size: 24pt; font-weight: 700; }
QLabel#metricCaption { color: #a1b0c2; font-size: 9pt; font-weight: 600; }
QLabel#feedback { min-height: 42px; font-size: 11pt; font-weight: 600; }
QFrame#metricCard, QFrame#studyCard, QFrame#surface, QFrame#levelCard {
    background: #1b2636; border: 1px solid #2b394c; border-radius: 16px;
}
QFrame#metricCard { min-height: 92px; }
QFrame#studyCard { min-height: 345px; }
QFrame#levelCard { min-height: 190px; }
QPushButton { background: #263549; color: #e3ebf6; border: 1px solid #36485f;
    border-radius: 10px; padding: 10px 16px; font-weight: 600; }
QPushButton:hover { background: #31445c; }
QPushButton:pressed { background: #3a506b; }
QPushButton:disabled { color: #718198; background: #1b2636; }
QPushButton#primaryButton { background: #4178e4; color: #ffffff; border: 0; }
QPushButton#primaryButton:hover { background: #5187ed; }
QPushButton#goodButton { background: #183b31; color: #8be0b4; border-color: #285a47; }
QPushButton#againButton { background: #402928; color: #ffaaa0; border-color: #66403c; }
QPushButton#hardButton { background: #40351f; color: #f4ca7c; border-color: #68552e; }
QPushButton#easyButton { background: #1d3150; color: #9ebcff; border-color: #334b72; }
QLineEdit, QComboBox { background: #192536; color: #e5edf8; border: 1px solid #35465c;
    border-radius: 9px; padding: 9px 11px; selection-background-color: #3f64a2; }
QComboBox QAbstractItemView { background: #192536; selection-background-color: #2d4262; }
QTabWidget::pane { border: 0; top: -1px; }
QTabBar::tab { background: transparent; color: #9cacbf; padding: 12px 17px;
    border-bottom: 2px solid transparent; font-weight: 600; }
QTabBar::tab:selected { color: #9ebcff; border-bottom: 2px solid #6995ef; }
QTableWidget { background: #1b2636; alternate-background-color: #182332; gridline-color: #2b394c;
    border: 1px solid #2b394c; border-radius: 10px; selection-background-color: #2c4264; }
QHeaderView::section { background: #202d3f; color: #a8b7c9; border: 0;
    border-bottom: 1px solid #35465c; padding: 10px; font-weight: 600; }
QProgressBar { background: #29374a; border: 0; border-radius: 6px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #6995ef; border-radius: 6px; }
QStatusBar { color: #9cacbf; }
"""


POS_TR = {
    "noun": "isim",
    "verb": "fiil",
    "adjective": "sıfat",
    "adverb": "zarf",
    "preposition": "edat",
    "pronoun": "zamir",
    "determiner": "belirleyici",
    "conjunction": "bağlaç",
    "exclamation": "ünlem",
    "conjunction/exclamation": "bağlaç / ünlem",
}


def _part_of_speech_tr(value: str) -> str:
    return POS_TR.get(value.casefold(), value)


def _card_frame(name: str = "surface") -> QFrame:
    frame = QFrame()
    frame.setObjectName(name)
    return frame


class MetricCard(QFrame):
    def __init__(self, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 13, 17, 13)
        layout.setSpacing(3)
        self.value = QLabel("0")
        self.value.setObjectName("metricValue")
        self.caption = QLabel(caption.upper())
        self.caption.setObjectName("metricCaption")
        layout.addWidget(self.value)
        layout.addWidget(self.caption)

    def set_value(self, value: int | str) -> None:
        self.value.setText(str(value))


class StudyPage(QWidget):
    progress_changed = Signal()

    def __init__(self, database: Database, audio: AudioManager) -> None:
        super().__init__()
        self.database = database
        self.audio = audio
        self.level: str | None = None
        self._seen_ids: set[int] = set()
        self._current: Word | None = None
        self._flipped = False
        self._build_ui()
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self.flip)
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 20)
        root.setSpacing(14)
        heading = QHBoxLayout()
        title = QLabel("Kelime kartları")
        title.setObjectName("sectionTitle")
        self.due_label = QLabel("Tekrar zamanı")
        self.due_label.setObjectName("eyebrow")
        heading.addWidget(title)
        heading.addStretch(1)
        heading.addWidget(self.due_label)
        root.addLayout(heading)

        self.card = _card_frame("studyCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(35, 26, 35, 27)
        card_layout.setSpacing(9)
        card_layout.addStretch(1)
        self.level_label = QLabel("")
        self.level_label.setObjectName("eyebrow")
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.word_label = QLabel("")
        self.word_label.setObjectName("wordTitle")
        self.word_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phonetics_label = QLabel("")
        self.phonetics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phonetics_label.setObjectName("subtitle")
        self.audio_button = QPushButton("Telaffuzu dinle")
        self.audio_button.clicked.connect(self._speak_current)
        self.audio_button.setMaximumWidth(230)
        audio_row = QHBoxLayout()
        audio_row.addStretch(1)
        audio_row.addWidget(self.audio_button)
        audio_row.addStretch(1)
        self.definition_label = QLabel("")
        self.definition_label.setObjectName("definition")
        self.definition_label.setWordWrap(True)
        self.definition_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.definition_label.hide()
        self.collocation_label = QLabel("")
        self.collocation_label.setWordWrap(True)
        self.collocation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.collocation_label.hide()
        self.example = QLabel("")
        self.example.setWordWrap(True)
        self.example.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.example.hide()
        self.show_button = QPushButton("Cevabı göster  ·  Boşluk")
        self.show_button.setObjectName("primaryButton")
        self.show_button.clicked.connect(self.flip)
        card_layout.addWidget(self.level_label)
        card_layout.addWidget(self.word_label)
        card_layout.addWidget(self.phonetics_label)
        card_layout.addLayout(audio_row)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.definition_label)
        card_layout.addWidget(self.collocation_label)
        card_layout.addWidget(self.example)
        card_layout.addStretch(1)
        card_layout.addWidget(self.show_button, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.card, 1)

        self.rating_row = QHBoxLayout()
        self.rating_row.setSpacing(10)
        self.again_button = self._rating_button("Tekrar\n< 1 dk", "againButton", Rating.AGAIN)
        self.hard_button = self._rating_button("Zor\n1 gün", "hardButton", Rating.HARD)
        self.good_button = self._rating_button("İyi\n3 gün", "goodButton", Rating.GOOD)
        self.easy_button = self._rating_button("Kolay\n5 gün", "easyButton", Rating.EASY)
        for button in (self.again_button, self.hard_button, self.good_button, self.easy_button):
            button.setMinimumHeight(54)
            button.hide()
            self.rating_row.addWidget(button, 1)
        root.addLayout(self.rating_row)

    def _rating_button(self, text: str, object_name: str, rating: Rating) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.clicked.connect(lambda _checked=False, value=rating: self._grade(value))
        return button

    def set_level(self, level: str | None) -> None:
        if self.level != level:
            self.level = level
            self._seen_ids.clear()
            self.refresh()

    def refresh(self) -> None:
        due = self.database.get_due_words(self.level, self._seen_ids)
        total = self.database.count_words(self.level)
        due_total = self.database.count_due_words(self.level)
        self.due_label.setText(f"{due_total} tekrar bekliyor · {total} kelime")
        if not due:
            self._current = None
            self._flipped = False
            self.word_label.setText("Bugünkü kartlar tamam")
            self.phonetics_label.setText("Şimdilik tekrar edilecek başka kart yok")
            self.level_label.setText("TEBRİKLER")
            self.audio_button.hide()
            self.definition_label.hide()
            self.collocation_label.hide()
            self.example.hide()
            self.show_button.setText("Kartları yenile")
            self.show_button.setEnabled(due_total > 0)
            self.show_button.show()
            for button in (self.again_button, self.hard_button, self.good_button, self.easy_button):
                button.hide()
            if due_total == 0:
                self.phonetics_label.setText("Tekrar zamanı gelen kelime yok. Kütüphaneye göz atabilir veya kelime ekleyebilirsin.")
            return
        self._current = due[0]
        self._flipped = False
        word = self._current
        self.level_label.setText(f"{word.cefr_level}  ·  {_part_of_speech_tr(word.part_of_speech).upper()}")
        self.word_label.setText(word.word)
        self.phonetics_label.setText(word.phonetics or "Telaffuzu ses düğmesinden dinleyebilirsin")
        self.audio_button.show()
        self.definition_label.setText(word.definition)
        self.collocation_label.setText(f"Sık kullanılan kelime birliktelikleri:  {word.collocations}" if word.collocations else "")
        self.example.setText(self._highlight_example(word))
        self.example.setTextFormat(Qt.TextFormat.RichText)
        self.definition_label.hide()
        self.collocation_label.setVisible(bool(word.collocations))
        self.example.hide()
        self.show_button.setText("Cevabı göster  ·  Boşluk")
        self.show_button.setEnabled(True)
        self.show_button.show()
        for button in (self.again_button, self.hard_button, self.good_button, self.easy_button):
            button.show()
            button.setEnabled(False)

    @staticmethod
    def _highlight_example(word: Word) -> str:
        safe = html.escape(word.example_sentence)
        pattern = re.compile(rf"\b{re.escape(word.word)}\b", re.IGNORECASE)
        return pattern.sub(
            lambda match: f'<span style="color:#3975df;font-weight:700">{match.group(0)}</span>',
            safe,
        )

    def flip(self) -> None:
        if self._current is None:
            self._seen_ids.clear()
            self.refresh()
            return
        if self._flipped:
            return
        self._flipped = True
        self.definition_label.show()
        self.collocation_label.setVisible(bool(self._current.collocations))
        self.example.show()
        self.show_button.hide()
        for button in (self.again_button, self.hard_button, self.good_button, self.easy_button):
            button.setEnabled(True)

    def _speak_current(self) -> None:
        if self._current:
            self.audio.speak(self._current.word)

    def _grade(self, rating: Rating) -> None:
        if not self._current or not self._flipped:
            return
        try:
            self.database.review_word(self._current.id, rating)
        except DatabaseError as exc:
            QMessageBox.critical(self, "İlerleme kaydedilemedi", str(exc))
            return
        self._seen_ids.add(self._current.id)
        self.progress_changed.emit()
        self.refresh()


class QuizPage(QWidget):
    progress_changed = Signal()

    def __init__(self, database: Database, audio: AudioManager) -> None:
        super().__init__()
        self.database = database
        self.audio = audio
        self.level: str | None = None
        self._word: Word | None = None
        self._answered = False
        self.choice_buttons: list[QPushButton] = []
        self._build_ui()
        self.new_question()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 20)
        root.setSpacing(16)
        heading = QHBoxLayout()
        title = QLabel("Alıştırma")
        title.setObjectName("sectionTitle")
        heading.addWidget(title)
        heading.addStretch(1)
        self.mode = QComboBox()
        self.mode.addItems(["Tanımı eşleştir", "Cümlede boşluk · B1", "Dinleyerek yazma"])
        self.mode.currentIndexChanged.connect(self.new_question)
        self.mode.setMinimumWidth(230)
        heading.addWidget(self.mode)
        root.addLayout(heading)

        self.prompt_card = _card_frame("surface")
        prompt_layout = QVBoxLayout(self.prompt_card)
        prompt_layout.setContentsMargins(26, 26, 26, 24)
        prompt_layout.setSpacing(14)
        self.instruction = QLabel("")
        self.instruction.setObjectName("eyebrow")
        self.instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prompt = QLabel("")
        self.prompt.setObjectName("definition")
        self.prompt.setWordWrap(True)
        self.prompt.setMinimumHeight(78)
        self.prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.listen_button = QPushButton("Kelimeyi dinle")
        self.listen_button.setMaximumWidth(200)
        self.listen_button.clicked.connect(self._play_prompt_word)
        listen_row = QHBoxLayout()
        listen_row.addStretch(1)
        listen_row.addWidget(self.listen_button)
        listen_row.addStretch(1)
        prompt_layout.addWidget(self.instruction)
        prompt_layout.addWidget(self.prompt)
        prompt_layout.addLayout(listen_row)
        root.addWidget(self.prompt_card)

        self.choices_container = QWidget()
        self.choices_layout = QGridLayout(self.choices_container)
        self.choices_layout.setContentsMargins(0, 0, 0, 0)
        self.choices_layout.setSpacing(9)
        root.addWidget(self.choices_container)

        self.spelling_row = QWidget()
        spelling_layout = QHBoxLayout(self.spelling_row)
        spelling_layout.setContentsMargins(0, 0, 0, 0)
        self.spelling_input = QLineEdit()
        self.spelling_input.setPlaceholderText("Duyduğun kelimeyi yaz")
        self.spelling_input.returnPressed.connect(self._submit_spelling)
        self.submit_button = QPushButton("Yazımı kontrol et")
        self.submit_button.setObjectName("primaryButton")
        self.submit_button.clicked.connect(self._submit_spelling)
        spelling_layout.addWidget(self.spelling_input, 1)
        spelling_layout.addWidget(self.submit_button)
        self.spelling_row.hide()
        root.addWidget(self.spelling_row)

        self.feedback = QLabel("")
        self.feedback.setObjectName("feedback")
        self.feedback.setWordWrap(True)
        self.feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.feedback)
        self.next_button = QPushButton("Sonraki soru")
        self.next_button.setObjectName("primaryButton")
        self.next_button.clicked.connect(self.new_question)
        root.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addStretch(1)

    def set_level(self, level: str | None) -> None:
        self.level = level
        self.new_question()

    def _clear_choices(self) -> None:
        while self.choices_layout.count():
            item = self.choices_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.choice_buttons.clear()

    def new_question(self, *_args: object) -> None:
        self._answered = False
        self.feedback.setText("")
        self.next_button.setEnabled(False)
        self._clear_choices()
        self.spelling_input.clear()
        self.spelling_input.setEnabled(True)
        self.submit_button.setEnabled(True)
        mode_index = self.mode.currentIndex()
        if mode_index == 1:
            pool = self.database.get_random_b1_words(1)
            self.instruction.setText("CÜMLEYİ TAMAMLAYAN KELİMEYİ SEÇ")
            self.listen_button.hide()
            self.spelling_row.hide()
            self.choices_container.show()
        elif mode_index == 2:
            pool = self.database.get_random_words(self.level, 1)
            self.instruction.setText("DİNLE VE KELİMEYİ YAZ")
            self.listen_button.show()
            self.spelling_row.show()
            self.choices_container.hide()
        else:
            pool = self.database.get_random_words(self.level, 1)
            self.instruction.setText("ANLAMA UYAN KELİMEYİ SEÇ")
            self.listen_button.hide()
            self.spelling_row.hide()
            self.choices_container.show()
        if not pool:
            self._word = None
            self.prompt.setText("Alıştırmaya başlamak için önce kelime ekle.")
            self.next_button.setEnabled(False)
            return
        self._word = pool[0]
        if mode_index == 1:
            self.prompt.setText(self._sentence_with_gap(self._word))
        elif mode_index == 2:
            self.prompt.setText("Kelime gizli. Ses kaydını istediğin kadar dinleyebilirsin.")
        else:
            self.prompt.setText(self._word.definition)
        if mode_index in (0, 1):
            self._show_choices(mode_index)
        elif mode_index == 2:
            self.listen_button.show()
            self.audio.speak(self._word.word)
            self.spelling_input.setFocus()

    @staticmethod
    def _sentence_with_gap(word: Word) -> str:
        safe = word.example_sentence
        pattern = re.compile(rf"\b{re.escape(word.word)}\b", re.IGNORECASE)
        return pattern.sub("________", safe, count=1)

    def _show_choices(self, mode_index: int) -> None:
        assert self._word is not None
        level = "B1" if mode_index == 1 else self.level
        choices = [self._word]
        for candidate in self.database.get_random_words(level, 20):
            if candidate.id != self._word.id and all(item.id != candidate.id for item in choices):
                choices.append(candidate)
            if len(choices) == 4:
                break
        random.shuffle(choices)
        for index, choice in enumerate(choices):
            button = QPushButton(choice.word)
            button.setMinimumHeight(45)
            button.clicked.connect(
                lambda _checked=False, selected=choice: self._answer_choice(selected)
            )
            self.choice_buttons.append(button)
            self.choices_layout.addWidget(button, index // 2, index % 2)

    def _play_prompt_word(self) -> None:
        if self._word:
            self.audio.speak(self._word.word)

    def _answer_choice(self, selected: Word) -> None:
        if not self._word or self._answered:
            return
        correct = selected.id == self._word.id
        self._finish_answer(correct, "cümle boşluğu" if self.mode.currentIndex() == 1 else "tanım alıştırması")
        for button in self.choice_buttons:
            button.setEnabled(False)
            if button.text() == self._word.word:
                button.setStyleSheet("border: 2px solid #52a578; font-weight: 700;")
            elif button.text() == selected.word and not correct:
                button.setStyleSheet("border: 2px solid #d16a61;")

    def _submit_spelling(self) -> None:
        if not self._word or self._answered:
            return
        correct = self.spelling_input.text().strip().casefold() == self._word.word.casefold()
        self._finish_answer(correct, "spelling")
        self.spelling_input.setEnabled(False)
        self.submit_button.setEnabled(False)

    def _finish_answer(self, correct: bool, mode: str) -> None:
        assert self._word is not None
        self._answered = True
        try:
            self.database.record_practice(self._word.id, correct, mode)
        except DatabaseError as exc:
            QMessageBox.critical(self, "Alıştırma kaydedilemedi", str(exc))
        word = html.escape(self._word.word)
        definition = html.escape(self._word.definition)
        if correct:
            self.feedback.setText(f"Doğru!  {word} — {definition}")
            self.feedback.setStyleSheet("color: #3b9a68;")
        else:
            self.feedback.setText(f"Doğru cevap: {word} — {definition}")
            self.feedback.setStyleSheet("color: #c65b52;")
        self.feedback.setTextFormat(Qt.TextFormat.RichText)
        self.next_button.setEnabled(True)
        self.progress_changed.emit()


class AddWordDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Yeni kelime ekle")
        self.setMinimumWidth(490)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.word = QLineEdit()
        self.word.setPlaceholderText("Örn. curious")
        self.level = QComboBox()
        self.level.addItems(["A2", "B1"])
        self.pos = QLineEdit()
        self.pos.setPlaceholderText("İngilizce: noun, verb, adjective…")
        self.phonetics = QLineEdit()
        self.phonetics.setPlaceholderText("İsteğe bağlı IPA telaffuzu")
        self.definition = QLineEdit()
        self.definition.setPlaceholderText("Kısa ve basit İngilizce tanım")
        self.example = QLineEdit()
        self.example.setPlaceholderText("Anlaşılır bir örnek cümle")
        self.collocations = QLineEdit()
        self.collocations.setPlaceholderText("İsteğe bağlı; noktalı virgülle ayır")
        form.addRow("Kelime", self.word)
        form.addRow("CEFR seviyesi", self.level)
        form.addRow("Sözcük türü (İngilizce)", self.pos)
        form.addRow("Telaffuz (IPA)", self.phonetics)
        form.addRow("İngilizce tanım", self.definition)
        form.addRow("Örnek cümle", self.example)
        form.addRow("Yaygın kelime birliktelikleri", self.collocations)
        layout.addLayout(form)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #cb5148;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("İptal")
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Kaydet")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        if not self.word.text().strip():
            self.error_label.setText("Devam etmek için bir kelime yaz.")
            self.word.setFocus()
            return
        for label, field in (("Sözcük türü", self.pos), ("Tanım", self.definition), ("Örnek cümle", self.example)):
            if not field.text().strip():
                self.error_label.setText(f"{label} gerekli.")
                field.setFocus()
                return
        self.accept()

    def values(self) -> dict[str, str]:
        return {
            "word": self.word.text(), "cefr_level": self.level.currentText(),
            "part_of_speech": self.pos.text(), "phonetics": self.phonetics.text(),
            "definition": self.definition.text(), "example_sentence": self.example.text(),
            "collocations": self.collocations.text(),
        }


class WordLibraryPage(QWidget):
    words_changed = Signal()

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.level: str | None = None
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 20)
        root.setSpacing(15)
        heading = QHBoxLayout()
        title = QLabel("Kelime kütüphanesi")
        title.setObjectName("sectionTitle")
        heading.addWidget(title)
        heading.addStretch(1)
        self.add_button = QPushButton("Yeni kelime ekle")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self._add_word)
        heading.addWidget(self.add_button)
        root.addLayout(heading)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Kelime, anlam veya sözcük türü ara…")
        self.search.textChanged.connect(lambda _text: self.refresh())
        self.count = QLabel("")
        self.count.setObjectName("eyebrow")
        filters.addWidget(self.search, 1)
        filters.addWidget(self.count)
        root.addLayout(filters)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["KELİME", "SEVİYE", "SÖZCÜK TÜRÜ", "DURUM", "TEKRAR", "SONRAKİ TEKRAR"])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(90)
        self.table.setColumnWidth(0, 175)
        self.table.setColumnWidth(1, 75)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 125)
        self.table.setColumnWidth(4, 95)
        root.addWidget(self.table, 1)

    def set_level(self, level: str | None) -> None:
        self.level = level
        self.refresh()

    def refresh(self) -> None:
        words = self.database.list_words(self.level, self.search.text() if hasattr(self, "search") else "")
        self.count.setText(f"{len(words)} kelime")
        self.table.setRowCount(len(words))
        for row_index, word in enumerate(words):
            mastery = self.database.mastery_for(word)
            display_mastery = {"New": "Yeni", "Learning": "Öğreniliyor", "Learned": "Öğrenildi"}[mastery]
            due = self._format_review(word.next_review)
            cells = [word.word, word.cefr_level, _part_of_speech_tr(word.part_of_speech).title(), mastery, str(word.repetitions), due]
            for col, text in enumerate(cells):
                if col == 3:
                    text = display_mastery
                item = QTableWidgetItem(text)
                if col in (1, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 3:
                    color = {"Yeni": "#74839a", "Öğreniliyor": "#d18a2c", "Öğrenildi": "#319263"}[display_mastery]
                    item.setForeground(QBrush(QColor(color)))
                    item.setToolTip(f"Öğrenme durumu: {display_mastery}")
                    item.setData(Qt.ItemDataRole.UserRole, color)
                self.table.setItem(row_index, col, item)
        self.table.resizeRowsToContents()

    @staticmethod
    def _format_review(value: str) -> str:
        try:
            due = datetime.fromisoformat(value)
            local = due.astimezone()
            if local <= datetime.now().astimezone():
                return "Tekrar zamanı"
            return local.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            return "Planlanmadı"

    def _add_word(self) -> None:
        dialog = AddWordDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.database.add_word(**dialog.values())
        except ValueError as exc:
            QMessageBox.warning(self, "Kelime eklenmedi", str(exc))
            return
        except DatabaseError as exc:
            QMessageBox.critical(self, "Kelime kaydedilemedi", str(exc))
            return
        self.search.clear()
        self.refresh()
        self.words_changed.emit()


class ProgressPage(QWidget):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 20)
        outer.setSpacing(16)
        title = QLabel("İlerlemen")
        title.setObjectName("sectionTitle")
        outer.addWidget(title)
        self.level_cards: dict[str, tuple[QProgressBar, QLabel]] = {}
        row = QHBoxLayout()
        row.setSpacing(14)
        for level in ("A2", "B1"):
            card = _card_frame("levelCard")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(19, 17, 19, 17)
            name = QLabel(f"{level} kelimeleri")
            name.setObjectName("sectionTitle")
            name.setStyleSheet("font-size: 15pt;")
            counts = QLabel("")
            counts.setWordWrap(True)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            layout.addWidget(name)
            layout.addWidget(QLabel("Birden fazla tekrarla öğrenilen kelimeler"))
            layout.addWidget(bar)
            layout.addWidget(counts)
            layout.addStretch(1)
            self.level_cards[level] = (bar, counts)
            row.addWidget(card, 1)
        outer.addLayout(row)
        note = QLabel("Bir kelime, art arda en az iki başarılı kart tekrarından sonra öğrenilmiş sayılır.\nDoğruluk oranı son 100 kart ve alıştırma yanıtına göre hesaplanır.")
        note.setObjectName("subtitle")
        note.setWordWrap(True)
        outer.addWidget(note)
        outer.addStretch(1)

    def refresh(self) -> None:
        for level, counts in self.database.level_progress().items():
            bar, label = self.level_cards[level]
            total = counts["total"]
            percentage = round((counts["learned"] / total) * 100) if total else 0
            bar.setValue(percentage)
            label.setText(
                f"{counts['learned']} öğrenildi   ·   {counts['learning']} öğreniliyor   ·   "
                f"{counts['new']} yeni   ·   {total} toplam"
            )


class MainWindow(QMainWindow):
    def __init__(self, database: Database, cache_dir: Path, recovered: bool = False) -> None:
        super().__init__()
        self.database = database
        self.settings = QSettings("WordSpring", "VocabularyLearner")
        self.theme = self.settings.value("theme", "light")
        self.audio = AudioManager(cache_dir, self)
        self.setWindowTitle("WordSpring · İngilizce Kelime Öğrenme")
        self.setMinimumSize(970, 720)
        self.resize(1120, 850)
        self._build_ui()
        help_menu = self.menuBar().addMenu("Yardım")
        about_action = QAction("Hakkında ve lisanslar", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        self.audio.message.connect(lambda message: self.statusBar().showMessage(message, 6000))
        self.refresh_dashboard()
        self._apply_theme()
        if recovered:
            self.statusBar().showMessage(
                "Önceki kelime veritabanı hasarlıydı. Yeni bir veritabanı oluşturuldu; eski dosyanın kurtarma kopyası saklandı.",
                12000,
            )

    def _build_ui(self) -> None:
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(25, 18, 25, 11)
        root.setSpacing(15)
        header = QHBoxLayout()
        title_column = QVBoxLayout()
        title = QLabel("WordSpring")
        title.setObjectName("appTitle")
        subtitle = QLabel("İngilizceni geliştirmek için kısa bir günlük çalışma")
        subtitle.setObjectName("subtitle")
        title_column.addWidget(title)
        title_column.addWidget(subtitle)
        header.addLayout(title_column)
        header.addStretch(1)
        self.level_filter = QComboBox()
        self.level_filter.addItem("Tüm seviyeler", None)
        self.level_filter.addItem("A2 seviyesi", "A2")
        self.level_filter.addItem("B1 seviyesi", "B1")
        self.level_filter.setMinimumWidth(145)
        self.level_filter.currentIndexChanged.connect(self._level_changed)
        self.theme_button = QPushButton("Koyu tema")
        self.theme_button.clicked.connect(self._toggle_theme)
        header.addWidget(self.level_filter)
        header.addWidget(self.theme_button)
        root.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setSpacing(11)
        self.metric_learned = MetricCard("Öğrenilen kelime")
        self.metric_due = MetricCard("Bugünkü tekrar")
        self.metric_accuracy = MetricCard("Doğruluk oranı")
        self.metric_streak = MetricCard("Günlük seri")
        for card in (self.metric_learned, self.metric_due, self.metric_accuracy, self.metric_streak):
            metrics.addWidget(card, 1)
        root.addLayout(metrics)

        self.tabs = QTabWidget()
        self.study_page = StudyPage(self.database, self.audio)
        self.quiz_page = QuizPage(self.database, self.audio)
        self.library_page = WordLibraryPage(self.database)
        self.progress_page = ProgressPage(self.database)
        self.tabs.addTab(self.study_page, "Kelime kartları")
        self.tabs.addTab(self.quiz_page, "Alıştırma")
        self.tabs.addTab(self.library_page, "Kütüphane")
        self.tabs.addTab(self.progress_page, "İlerleme")
        root.addWidget(self.tabs, 1)
        self.setCentralWidget(content)
        self.study_page.progress_changed.connect(self.refresh_dashboard)
        self.study_page.progress_changed.connect(self.progress_page.refresh)
        self.study_page.progress_changed.connect(self.library_page.refresh)
        self.quiz_page.progress_changed.connect(self.refresh_dashboard)
        self.quiz_page.progress_changed.connect(self.progress_page.refresh)
        self.library_page.words_changed.connect(self._words_added)

    def _level_changed(self, _index: int) -> None:
        level = self.level_filter.currentData()
        self.study_page.set_level(level)
        self.quiz_page.set_level(level)
        self.library_page.set_level(level)

    def _words_added(self) -> None:
        self.refresh_dashboard()
        level = self.level_filter.currentData()
        self.study_page.set_level(level)
        self.study_page.refresh()
        self.progress_page.refresh()

    def refresh_dashboard(self) -> None:
        stats = self.database.dashboard()
        self.metric_learned.set_value(stats["learned"])
        self.metric_due.set_value(stats["due"])
        self.metric_accuracy.set_value(f"{stats['accuracy']}%")
        self.metric_streak.set_value(f"{stats['streak']} gün")

    def _toggle_theme(self) -> None:
        self.theme = "dark" if self.theme != "dark" else "light"
        self.settings.setValue("theme", self.theme)
        self._apply_theme()

    def _apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(DARK_QSS if self.theme == "dark" else LIGHT_QSS)
        self.theme_button.setText("Açık tema" if self.theme == "dark" else "Koyu tema")

    def _show_about(self) -> None:
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        notice_path = bundle_root / "THIRD_PARTY_NOTICES.md"
        try:
            notices = notice_path.read_text(encoding="utf-8")
        except OSError:
            notices = f"Kaynak ve lisans bildirimleri: {notice_path}"
        license_parts: list[str] = []
        for license_root in (bundle_root / "Licenses", bundle_root.parent / "Licenses"):
            if not license_root.is_dir():
                continue
            for license_path in sorted(license_root.glob("*.txt")):
                try:
                    license_parts.append(f"{license_path.name}\n\n{license_path.read_text(encoding='utf-8')}")
                except OSError:
                    continue
        if license_parts:
            notices += "\n\nTHIRD-PARTY LICENSE TEXTS\n\n" + "\n\n".join(license_parts)
        app = QApplication.instance()
        version = app.applicationVersion() if app else ""
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setWindowTitle("WordSpring hakkında")
        dialog.setText(f"WordSpring {version}\nTürkçe arayüzlü A2–B1 İngilizce kelime çalışması")
        dialog.setInformativeText(
            "500 kelime: 250 A2 ve 250 B1. Çalışma ilerlemeniz bu bilgisayarda saklanır. "
            "Açıklamalar ve örnek cümleler İngilizcedir."
        )
        dialog.setDetailedText(notices)
        dialog.exec()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.audio.close()
        self.database.close()
        super().closeEvent(event)


def show_startup_error(error: Exception) -> None:
    _app = QApplication.instance() or QApplication([])
    QMessageBox.critical(
        None,
        "WordSpring başlatılamadı",
        "Uygulama başlatılamadı.\n\n"
        f"{error}\n\n"
        "Windows kullanıcı verileri klasörüne yazma iznini kontrol edip uygulamayı yeniden başlat.",
    )
