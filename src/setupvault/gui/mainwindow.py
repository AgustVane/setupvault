from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QCloseEvent, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from setupvault.gui.pages import BasePage, PlaceholderPage
from setupvault.gui.panels import (
    DiffPanel,
    DoctorPanel,
    ExportPanel,
    InfoPanel,
    ListPanel,
    ReportPanel,
    RestorePanel,
    SettingsPanel,
    ValidatePanel,
)
from setupvault.gui.settings import GuiSettings
from setupvault.gui.styles import Theme, resolve_theme, stylesheet

if TYPE_CHECKING:
    from collections.abc import Mapping

_COMMAND_LABELS = [
    ("export", "Export", "\u2b06", "Capture system configuration (Ctrl+1)"),
    ("restore", "Restore", "\u2b07", "Restore a snapshot (Ctrl+2)"),
    ("info", "Info", "\u2139", "View snapshot details (Ctrl+3)"),
    ("validate", "Validate", "\u2713", "Validate a snapshot (Ctrl+4)"),
    ("report", "Report", "\u25a3", "Generate a report (Ctrl+5)"),
    ("doctor", "Doctor", "\u2795", "Run diagnostics (Ctrl+6)"),
    ("diff", "Diff", "\u21c4", "Compare snapshots (Ctrl+7)"),
    ("list", "List", "\u2630", "List all snapshots (Ctrl+8)"),
    ("settings", "Settings", "\u2699", "Customize appearance & defaults (Ctrl+9)"),
]


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: GuiSettings | None = None,
        theme: Theme | None = None,
        pages: Mapping[str, BasePage] | None = None,
    ) -> None:
        super().__init__()
        self._settings = settings or GuiSettings.load()
        self._theme = theme or resolve_theme(self._settings.theme, self._settings.accent)
        self.setWindowTitle("SetupVault")
        icon_path = Path(__file__).parent / "assets" / "setupvault.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(720, 480)
        self._build_ui(pages or {})
        self._install_shortcuts()
        self._restore_geometry()

    def _build_ui(self, pages: Mapping[str, BasePage]) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        brand = QFrame()
        brand.setObjectName("Brand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(16, 20, 16, 16)
        brand_layout.setSpacing(2)
        brand_title = QLabel("SetupVault")
        brand_title.setObjectName("AppTitle")
        brand_layout.addWidget(brand_title)
        brand_sub = QLabel("Portable Linux\nconfiguration snapshots")
        brand_sub.setObjectName("AppSubtitle")
        brand_layout.addWidget(brand_sub)
        sb_layout.addWidget(brand)

        self._nav = QListWidget()
        self._nav.setFrameShape(QFrame.Shape.NoFrame)
        self._nav.setObjectName("Nav")
        for _key, label, icon, tip in _COMMAND_LABELS:
            item = QListWidgetItem(f"{icon}  {label}")
            item.setData(Qt.ItemDataRole.UserRole, _key)
            item.setToolTip(tip)
            self._nav.addItem(item)
        sb_layout.addWidget(self._nav, 1)

        footer = QLabel()
        footer.setObjectName("SidebarFooter")
        footer.setWordWrap(True)

        import platform

        try:
            import distro

            distro_name = distro.name(pretty=True)
        except Exception:
            distro_name = platform.system()

        footer.setText(f"{distro_name}\nv0.1.0 \u00b7 Ready")
        footer.setContentsMargins(16, 8, 16, 16)
        sb_layout.addWidget(footer)

        root.addWidget(sidebar)

        self._stack = QStackedWidget()
        panel_for = {
            "export": ExportPanel,
            "restore": RestorePanel,
            "info": InfoPanel,
            "validate": ValidatePanel,
            "report": ReportPanel,
            "doctor": DoctorPanel,
            "diff": DiffPanel,
            "list": ListPanel,
            "settings": SettingsPanel,
        }
        for key, label, _icon, _tip in _COMMAND_LABELS:
            page = pages.get(key)
            if page is None:
                cls = panel_for.get(key)
                page = cls() if cls else PlaceholderPage(label)
            if hasattr(page, "apply_settings"):
                page.apply_settings(self._settings)
            self._stack.addWidget(page)

        root.addWidget(self._stack, 1)
        self.setCentralWidget(central)

        self._nav.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._nav.setCurrentRow(0)
        self.apply_theme(self._theme)

        status = self.statusBar()
        status.setObjectName("StatusBar")
        status.showMessage("Ready")

    def _install_shortcuts(self) -> None:
        for i in range(1, min(10, len(_COMMAND_LABELS) + 1)):
            QShortcut(QKeySequence(f"Ctrl+{i}"), self).activated.connect(
                lambda row=i - 1: self._nav.setCurrentRow(row)
            )

    def _restore_geometry(self) -> None:
        if self._settings.window_geometry:
            try:
                geo = QByteArray.fromBase64(self._settings.window_geometry.encode("ascii"))
                self.restoreGeometry(geo)
            except Exception:
                self.resize(960, 640)
        else:
            self.resize(960, 640)
        if self._settings.window_state:
            try:
                state = QByteArray.fromBase64(self._settings.window_state.encode("ascii"))
                self.restoreState(state)
            except Exception:
                pass

    def closeEvent(self, event: QCloseEvent) -> None:
        geo = bytes(self.saveGeometry().toBase64().data()).decode("ascii")
        state = bytes(self.saveState().toBase64().data()).decode("ascii")
        self._settings.window_geometry = geo
        self._settings.window_state = state
        self._settings.save()
        super().closeEvent(event)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.setStyleSheet(stylesheet(theme, self._settings.density))
        for idx in range(self._stack.count()):
            page = self._stack.widget(idx)
            if isinstance(page, BasePage):
                page.apply_theme(theme)

    def reload_settings(self) -> None:
        self._settings = GuiSettings.load()
        self._theme = resolve_theme(self._settings.theme, self._settings.accent)
        self.apply_theme(self._theme)
        for idx in range(self._stack.count()):
            page = self._stack.widget(idx)
            if page is not None and hasattr(page, "apply_settings"):
                page.apply_settings(self._settings)

    def show_status(self, message: str, timeout: int = 5000) -> None:
        self.statusBar().showMessage(message, timeout)
