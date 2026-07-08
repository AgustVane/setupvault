from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from setupvault.gui.widgets import Card

_PAGE_ICONS = {
    "Export": "\u2b06",
    "Restore": "\u2b07",
    "Info": "\u2139",
    "Validate": "\u2713",
    "Report": "\u25a3",
    "Doctor": "\u2795",
    "Diff": "\u21c4",
    "List": "\u2630",
    "Settings": "\u2699",
}


class BasePage(QWidget):
    title: str = "Untitled"
    description: str = ""

    def __init__(self, theme=None) -> None:
        super().__init__()
        self._theme = theme
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header.setObjectName("PageHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(28, 24, 28, 20)
        h_layout.setSpacing(12)

        icon = _PAGE_ICONS.get(self.title, "")
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            h_layout.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)
        title_label = QLabel(self.title)
        title_label.setObjectName("PageTitle")
        text_col.addWidget(title_label)

        if self.description:
            desc = QLabel(self.description)
            desc.setObjectName("PageDescription")
            desc.setWordWrap(True)
            text_col.addWidget(desc)

        h_layout.addLayout(text_col, 1)
        root.addWidget(header)

        body = QScrollArea()
        body.setWidgetResizable(True)
        body.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        self._body_layout = QVBoxLayout(inner)
        self._body_layout.setContentsMargins(28, 20, 28, 28)
        self._body_layout.setSpacing(20)
        self._body_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._build_body()
        body.setWidget(inner)
        root.addWidget(body, 1)

    def _build_body(self) -> None:
        pass

    def apply_theme(self, theme) -> None:
        self._theme = theme


class PlaceholderPage(BasePage):
    def __init__(self, label: str) -> None:
        self.title = label
        self.description = "This panel is not yet implemented."
        super().__init__()


class _StatePage(QWidget):
    def __init__(self, icon: str, title: str, description: str = "") -> None:
        super().__init__()
        self.setObjectName("StatePage")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        icon_label = QLabel(icon)
        icon_label.setObjectName("StateIcon")
        layout.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setObjectName("StateTitle")
        layout.addWidget(title_label)
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("StateDescription")
            desc_label.setWordWrap(True)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(desc_label)


class EmptyState(_StatePage):
    def __init__(self, title: str = "Nothing here", description: str = "") -> None:
        super().__init__("\u2205", title, description)


class ErrorState(_StatePage):
    def __init__(self, title: str = "Something went wrong", description: str = "") -> None:
        super().__init__("\u26a0", title, description)


class Section(Card):
    """A section group (aliased Card for backwards compat)."""

    def __init__(self, title: str, description: str = "") -> None:
        super().__init__(title=title, description=description)
