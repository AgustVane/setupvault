from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class Card(QFrame):
    """A rounded container with shadow and border."""

    def __init__(
        self, title: str = "", description: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(12)
        if title:
            self._title = QLabel(title)
            self._title.setObjectName("CardTitle")
            self._layout.addWidget(self._title)
        if description:
            self._desc = QLabel(description)
            self._desc.setObjectName("CardDesc")
            self._desc.setWordWrap(True)
            self._layout.addWidget(self._desc)

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def addLayout(self, layout: QVBoxLayout | QHBoxLayout) -> None:
        self._layout.addLayout(layout)

    def body(self) -> QVBoxLayout:
        return self._layout


class StatCard(QFrame):
    """A compact metric card (value + label)."""

    def __init__(self, value: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._value = QLabel(value)
        self._value.setObjectName("StatValue")
        self._value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._value)
        self._label = QLabel(label)
        self._label.setObjectName("StatLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

    def set_value(self, value: str) -> None:
        self._value.setText(value)


class LogItem(QFrame):
    """A single log entry with status icon and message."""

    STATUS_COLORS = {
        "info": "#6B7280",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "running": "#6366F1",
    }

    STATUS_ICONS = {
        "info": "\u2139",
        "success": "\u2713",
        "warning": "\u26a0",
        "error": "\u2717",
        "running": "\u25cf",
    }

    def __init__(self, message: str, status: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LogEntry")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(10)

        icon = self.STATUS_ICONS.get(status, "\u2139")
        color = self.STATUS_COLORS.get(status, "#6B7280")
        self._icon = QLabel(icon)
        self._icon.setObjectName("LogIcon")
        self._icon.setStyleSheet(f"color: {color};")
        self._icon.setFixedWidth(20)
        layout.addWidget(self._icon)

        self._msg = QLabel(message)
        self._msg.setObjectName("LogMessage")
        self._msg.setWordWrap(True)
        layout.addWidget(self._msg, 1)

        self._time = QLabel(datetime.now().strftime("%H:%M:%S"))
        self._time.setObjectName("LogTime")
        layout.addWidget(self._time)

    def set_message(self, message: str) -> None:
        self._msg.setText(message)


class StatusBadge(QLabel):
    """A small colored badge."""

    COLORS = {
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "info": "#6366F1",
        "neutral": "#6B7280",
    }

    def __init__(self, text: str, variant: str = "neutral", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("Badge")
        color = self.COLORS.get(variant, "#6B7280")
        self.setStyleSheet(f"background-color: {color}20; color: {color};")


class FilePicker(QWidget):
    """A text field with a "Browse" button."""

    def __init__(
        self,
        mode: str = "open",
        caption: str = "Select file",
        filter: str = "JSON (*.json);;All files (*)",
        placeholder: str = "",
    ) -> None:
        super().__init__()
        self._mode = mode
        self._caption = caption
        self._filter = filter

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._field = QLineEdit()
        self._field.setPlaceholderText(placeholder)
        layout.addWidget(self._field, 1)

        browse = QPushButton("Browse")
        browse.setObjectName("Secondary")
        browse.clicked.connect(self._browse)
        layout.addWidget(browse)

    def _browse(self) -> None:
        start = self.path() or str(Path.home())
        if self._mode == "save":
            path, _ = QFileDialog.getSaveFileName(self, self._caption, start, self._filter)
        else:
            path, _ = QFileDialog.getOpenFileName(self, self._caption, start, self._filter)
        if path:
            self._field.setText(path)

    def path(self) -> str:
        return self._field.text().strip()

    def set_path(self, path: str) -> None:
        self._field.setText(path)


class ComboField(QWidget):
    """A labelled combo box."""

    def __init__(self, label: str, options: list[str], default: str | None = None) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        lbl = QLabel(label)
        lbl.setFixedWidth(90)
        layout.addWidget(lbl)

        self._combo = QComboBox()
        self._combo.addItems(options)
        if default and default in options:
            self._combo.setCurrentText(default)
        layout.addWidget(self._combo, 1)

    def value(self) -> str:
        return self._combo.currentText()

    def set_value(self, value: str) -> None:
        self._combo.setCurrentText(value)


class LoadingIndicator(QWidget):
    """Indeterminate progress bar with a status message."""

    def __init__(self, text: str = "Working") -> None:
        super().__init__()
        self.setObjectName("LoadingIndicator")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setFixedWidth(160)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)
        self._label = QLabel(text)
        self._label.setObjectName("LoadingLabel")
        layout.addWidget(self._label)
        layout.addStretch()

    def set_text(self, text: str) -> None:
        self._label.setText(text)


class HtmlViewer(QDialog):
    """A dialog for rendering HTML content."""

    def __init__(self, html: str, title: str = "Report", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(720, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setHtml(html)
        layout.addWidget(self._browser, 1)
        bar = QWidget()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 8, 12, 8)
        bar_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("Secondary")
        close_btn.clicked.connect(self.accept)
        bar_layout.addWidget(close_btn)
        layout.addWidget(bar)
