from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    surface: str
    sidebar: str
    sidebar_text: str
    sidebar_muted: str
    sidebar_hover: str
    sidebar_active: str
    sidebar_active_text: str
    text: str
    text_muted: str
    border: str
    accent: str
    accent_hover: str
    accent_text: str
    success: str
    warning: str
    danger: str
    radius: str = "8px"
    radius_sm: str = "6px"
    font_family: str = '-apple-system, "Segoe UI", "Noto Sans", Cantarell, sans-serif'

    def with_accent(self, accent: str) -> Theme:
        return Theme(
            name=self.name,
            background=self.background,
            surface=self.surface,
            sidebar=self.sidebar,
            sidebar_text=self.sidebar_text,
            sidebar_muted=self.sidebar_muted,
            sidebar_hover=self.sidebar_hover,
            sidebar_active=self.sidebar_active,
            sidebar_active_text=self.sidebar_active_text,
            text=self.text,
            text_muted=self.text_muted,
            border=self.border,
            accent=accent,
            accent_hover=accent,
            accent_text=self.accent_text,
            success=self.success,
            warning=self.warning,
            danger=self.danger,
        )


LIGHT = Theme(
    name="light",
    background="#F8FAFC",
    surface="#FFFFFF",
    sidebar="#111827",
    sidebar_text="#F3F4F6",
    sidebar_muted="#9CA3AF",
    sidebar_hover="#1F2937",
    sidebar_active="#6366F1",
    sidebar_active_text="#FFFFFF",
    text="#111827",
    text_muted="#6B7280",
    border="#E5E7EB",
    accent="#6366F1",
    accent_hover="#4F46E5",
    accent_text="#FFFFFF",
    success="#10B981",
    warning="#F59E0B",
    danger="#EF4444",
)

DARK = Theme(
    name="dark",
    background="#0F1117",
    surface="#1A1D27",
    sidebar="#0A0C12",
    sidebar_text="#E5E7EB",
    sidebar_muted="#6B7280",
    sidebar_hover="#1F2937",
    sidebar_active="#6366F1",
    sidebar_active_text="#FFFFFF",
    text="#E5E7EB",
    text_muted="#9CA3AF",
    border="#2D3140",
    accent="#818CF8",
    accent_hover="#6366F1",
    accent_text="#FFFFFF",
    success="#34D399",
    warning="#FBBF24",
    danger="#F87171",
)


def get_theme(name: str) -> Theme:
    return {"light": LIGHT, "dark": DARK}.get(name, LIGHT)


def resolve_theme(name: str, accent: str = "") -> Theme:
    theme = get_theme(name)
    if accent:
        theme = theme.with_accent(accent)
    return theme


def stylesheet(theme: Theme, density: str = "comfortable") -> str:
    font_size = "12px" if density == "compact" else "13px"
    title_size = "16px" if density == "compact" else "18px"
    heading_size = "14px" if density == "compact" else "15px"
    small_size = "11px" if density == "compact" else "12px"
    pad = "6px 10px" if density == "compact" else "8px 14px"
    pad_sm = "4px 8px" if density == "compact" else "6px 12px"

    return f"""
    QWidget {{
        background-color: {theme.background};
        color: {theme.text};
        font-size: {font_size};
        font-family: {theme.font_family};
    }}
    QMainWindow {{
        background-color: {theme.background};
    }}
    QFrame#Sidebar {{
        background-color: {theme.sidebar};
        border: none;
    }}
    QFrame#Sidebar QLabel {{
        background-color: transparent;
    }}
    QFrame#PageHeader QLabel {{
        background-color: transparent;
    }}
    QFrame#Brand {{
        background-color: transparent;
        border: none;
        padding: 20px 16px 16px 16px;
    }}
    QLabel#AppTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {theme.sidebar_text};
        letter-spacing: 0.3px;
    }}
    QLabel#AppSubtitle {{
        font-size: 11px;
        color: {theme.sidebar_muted};
        margin-top: 2px;
    }}
    QListWidget#Nav {{
        background-color: transparent;
        border: none;
        padding: 8px 8px;
        outline: none;
    }}
    QListWidget#Nav QScrollBar:vertical, QListWidget#Nav QScrollBar:horizontal {{
        width: 0;
        height: 0;
        background: transparent;
    }}
    QListWidget#Nav::item {{
        padding: 10px 12px;
        border-radius: {theme.radius_sm};
        color: {theme.sidebar_text};
        font-size: {font_size};
        margin: 2px 0;
    }}
    QListWidget#Nav::item:hover {{
        background-color: {theme.sidebar_hover};
    }}
    QListWidget#Nav::item:selected {{
        background-color: {theme.sidebar_active};
        color: {theme.sidebar_active_text};
        font-weight: 600;
    }}
    QLabel#SidebarFooter {{
        color: {theme.sidebar_muted};
        font-size: 11px;
        padding: 8px 16px 12px 16px;
    }}
    QFrame#PageHeader {{
        background-color: {theme.surface};
        border: none;
        padding: 24px 28px 20px 28px;
    }}
    QLabel#PageTitle {{
        font-size: {title_size};
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#PageDescription {{
        font-size: {small_size};
        color: {theme.text_muted};
        margin-top: 4px;
        line-height: 1.4;
    }}
    QFrame#Card {{
        background-color: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: {theme.radius};
        padding: 20px;
    }}
    QLabel#CardTitle {{
        font-size: {heading_size};
        font-weight: 600;
        color: {theme.text};
        margin-bottom: 4px;
    }}
    QLabel#CardDesc {{
        font-size: {small_size};
        color: {theme.text_muted};
    }}
    QFrame#StatCard {{
        background-color: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: {theme.radius};
        padding: 16px;
    }}
    QLabel#StatValue {{
        font-size: 22px;
        font-weight: 700;
        color: {theme.text};
    }}
    QLabel#StatLabel {{
        font-size: 11px;
        color: {theme.text_muted};
        font-weight: 500;
        text-transform: uppercase;
    }}
    QPushButton {{
        background-color: {theme.surface};
        color: {theme.text};
        border: 1px solid {theme.border};
        border-radius: {theme.radius_sm};
        padding: {pad};
        font-weight: 500;
    }}
    QPushButton:hover {{
        border-color: {theme.accent};
        background-color: {theme.background};
    }}
    QPushButton:pressed {{
        background-color: {theme.border};
    }}
    QPushButton:disabled {{
        opacity: 0.5;
        color: {theme.text_muted};
    }}
    QPushButton#Primary {{
        background-color: {theme.accent};
        color: {theme.accent_text};
        border: none;
        font-weight: 600;
        padding: {pad};
    }}
    QPushButton#Primary:hover {{
        background-color: {theme.accent_hover};
    }}
    QPushButton#Primary:pressed {{
        background-color: {theme.accent_hover};
    }}
    QPushButton#Primary:disabled {{
        background-color: {theme.border};
        color: {theme.text_muted};
    }}
    QPushButton#Secondary {{
        background-color: transparent;
        color: {theme.text};
        border: 1px solid {theme.border};
        border-radius: {theme.radius_sm};
        padding: {pad};
        font-weight: 500;
    }}
    QPushButton#Secondary:hover {{
        border-color: {theme.accent};
        color: {theme.accent};
    }}
    QPushButton#Ghost {{
        background-color: transparent;
        color: {theme.text_muted};
        border: none;
        border-radius: {theme.radius_sm};
        padding: {pad_sm};
        font-weight: 400;
    }}
    QPushButton#Ghost:hover {{
        background-color: {theme.background};
        color: {theme.text};
    }}
    QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
        background-color: {theme.surface};
        color: {theme.text};
        border: 1px solid {theme.border};
        border-radius: {theme.radius_sm};
        padding: 8px 12px;
        selection-background-color: {theme.accent};
        selection-color: {theme.accent_text};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{
        border-color: {theme.accent};
    }}
    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {theme.text_muted};
        margin-right: 4px;
    }}
    QCheckBox {{
        spacing: 10px;
        font-size: {font_size};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {theme.border};
        border-radius: 4px;
        background-color: {theme.surface};
    }}
    QCheckBox::indicator:checked {{
        background-color: {theme.accent};
        border-color: {theme.accent};
    }}
    QCheckBox::indicator:hover {{
        border-color: {theme.accent};
    }}
    QListWidget {{
        background-color: {theme.surface};
        color: {theme.text};
        border: 1px solid {theme.border};
        border-radius: {theme.radius_sm};
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px 12px;
        border-radius: 4px;
    }}
    QListWidget::item:hover {{
        background-color: {theme.background};
    }}
    QListWidget::item:selected {{
        background-color: {theme.accent};
        color: {theme.accent_text};
    }}
    QProgressBar {{
        background-color: {theme.border};
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {theme.accent};
        border-radius: 4px;
    }}
    QStatusBar {{
        background-color: {theme.surface};
        color: {theme.text_muted};
        border-top: 1px solid {theme.border};
        font-size: 12px;
        padding: 4px 16px;
    }}
    QStatusBar::item {{
        border: none;
    }}
    QGroupBox {{
        border: 1px solid {theme.border};
        border-radius: {theme.radius};
        margin-top: 12px;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        color: {theme.text_muted};
        subcontrol-origin: margin;
        left: 10px;
    }}
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {theme.border};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {theme.text_muted};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {theme.border};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {theme.text_muted};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QWidget#LoadingIndicator {{
        background-color: transparent;
        padding: 8px 0;
    }}
    QLabel#LoadingLabel {{
        color: {theme.text_muted};
        font-size: 12px;
    }}
    QWidget#StatePage {{
        background-color: transparent;
    }}
    QLabel#StateIcon {{
        font-size: 32px;
        color: {theme.text_muted};
    }}
    QLabel#StateTitle {{
        font-size: 16px;
        font-weight: 600;
        color: {theme.text};
    }}
    QLabel#StateDescription {{
        font-size: 13px;
        color: {theme.text_muted};
        max-width: 400px;
    }}
    QLabel#Badge {{
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 600;
    }}
    QFrame#LogEntry {{
        background-color: transparent;
        border: none;
        padding: 6px 0;
    }}
    QLabel#LogIcon {{
        font-size: 14px;
        min-width: 20px;
    }}
    QLabel#LogMessage {{
        font-size: 13px;
        color: {theme.text};
    }}
    QLabel#LogTime {{
        font-size: 11px;
        color: {theme.text_muted};
    }}
    QFrame#Section {{
        background-color: {theme.surface};
        border: 1px solid {theme.border};
        border-radius: {theme.radius};
    }}
    QLabel#SectionTitle {{
        font-size: {heading_size};
        font-weight: 600;
        color: {theme.text};
    }}
    QLabel#SectionDesc {{
        font-size: 12px;
        color: {theme.text_muted};
    }}
    QDialog {{
        background-color: {theme.background};
    }}
    """
