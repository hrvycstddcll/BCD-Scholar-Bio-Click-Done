_LIGHT = dict(
    BG           = "#F4F5F7",
    PANEL_BG     = "#FFFFFF",
    CARD_BG      = "#FFFFFF",
    INPUT_BG     = "#F9FAFB",
    ACCENT       = "#F59E0B",
    ACCENT2      = "#FBBF24",
    ACCENT3      = "#F97316",
    SUCCESS      = "#059669",
    DANGER       = "#DC2626",
    TEXT_PRIMARY = "#111827",
    TEXT_MUTED   = "#6B7280",
    BORDER       = "#D1D5DB",
    ALT_ROW      = "#F9FAFB",
    SCROLLBAR    = "#D1D5DB",
)

_DARK = dict(
    BG           = "#0E0F13",
    PANEL_BG     = "#16181F",
    CARD_BG      = "#1E2029",
    INPUT_BG     = "#252736",
    ACCENT       = "#F59E0B",
    ACCENT2      = "#FBBF24",
    ACCENT3      = "#F97316",
    SUCCESS      = "#10B981",
    DANGER       = "#EF4444",
    TEXT_PRIMARY = "#F5F5F0",
    TEXT_MUTED   = "#9CA3AF",
    BORDER       = "#2A2D3A",
    ALT_ROW      = "#191B24",
    SCROLLBAR    = "#2A2D3A",
)

_current = _LIGHT.copy()

# ── Shared constants ──────────────────────────────────────────
AMBER  = "#F59E0B"
ORANGE = "#F97316"

CAT_ICONS = {
    "Electronics":           "⚡",
    "Clothing":              "👕",
    "Food & Beverage":       "🍎",
    "Office Supplies":       "📎",
    "Sports & Fitness":      "🏃",
    "Home & Garden":         "🏡",
    "Beauty & Personal Care":"✨",
    "Toys & Games":          "🎮",
    "Health & Wellness":     "💊",
    "Tools & Hardware":      "🔧",
}


def set_theme(dark: bool):
    _current.clear()
    _current.update(_DARK if dark else _LIGHT)


def is_dark() -> bool:
    return _current["BG"] == _DARK["BG"]


def c(key: str) -> str:
    return _current[key]


def combo_style(font_size: int = 13) -> str:
    """Standard amber-accent combo box — solid visible background."""
    bg  = c("INPUT_BG")
    txt = c("TEXT_PRIMARY")
    bd  = c("BORDER")
    card = c("CARD_BG")
    return (
        f"QComboBox{{background:{bg};border:1.5px solid {bd};"
        f"border-radius:10px;padding:0 14px;color:{txt};font-size:{font_size}px;"
        f"min-height:40px;}}"
        f"QComboBox:focus{{border:1.5px solid {AMBER};}}"
        f"QComboBox:on{{border:1.5px solid {AMBER};}}"
        f"QComboBox::drop-down{{border:none;background:rgba(245,158,11,0.12);"
        f"border-top-right-radius:9px;border-bottom-right-radius:9px;width:32px;}}"
        f"QComboBox::down-arrow{{image:none;width:0;height:0;"
        f"border-left:5px solid transparent;border-right:5px solid transparent;"
        f"border-top:6px solid {AMBER};}}"
        f"QComboBox QAbstractItemView{{background:{card};border:1.5px solid {bd};"
        f"border-radius:10px;outline:none;color:{txt};font-size:{font_size}px;"
        f"selection-background-color:rgba(245,158,11,0.18);}}"
        f"QComboBox QAbstractItemView::item{{padding:8px 14px;border:none;"
        f"min-height:32px;}}"
        f"QComboBox QAbstractItemView::item:hover{{background:rgba(245,158,11,0.12);"
        f"color:{AMBER};}}"
    )


def input_style(font_size: int = 13) -> str:
    """Standard amber-focus line-edit — solid visible background."""
    bg  = c("INPUT_BG")
    txt = c("TEXT_PRIMARY")
    bd  = c("BORDER")
    return (
        f"QLineEdit{{background:{bg};border:1.5px solid {bd};"
        f"border-radius:10px;padding:0 14px;"
        f"color:{txt};font-size:{font_size}px;min-height:40px;}}"
        f"QLineEdit:focus{{border:1.5px solid {AMBER};"
        f"background:{bg};}}"
    )


def spinbox_style(font_size: int = 14) -> str:
    """Standard amber-focus spinbox — solid visible background."""
    bg  = c("INPUT_BG")
    txt = c("TEXT_PRIMARY")
    bd  = c("BORDER")
    t   = "QSpinBox"
    return (
        f"{t}{{background:{bg};border:1.5px solid {bd};"
        f"border-radius:10px;padding:0 12px;"
        f"color:{txt};font-size:{font_size}px;font-weight:700;min-height:40px;}}"
        f"{t}:focus{{border:1.5px solid {AMBER};}}"
        f"{t}::up-button,{t}::down-button{{border:none;background:transparent;width:20px;}}"
    )


def dialog_style() -> str:
    """Consistent modal dialog style — opaque, themed, always readable."""
    bg  = c("CARD_BG")
    bd  = c("BORDER")
    txt = c("TEXT_PRIMARY")
    return (
        f"QDialog{{background:{bg};border:1.5px solid {bd};"
        f"border-radius:16px;color:{txt};}}"
        f"QLabel{{background:transparent;border:none;color:{txt};}}"
        f"QMessageBox{{background:{bg};color:{txt};}}"
    )


def msgbox_style() -> str:
    """QMessageBox — opaque card with amber accent buttons."""
    bg  = c("CARD_BG")
    bd  = c("BORDER")
    txt = c("TEXT_PRIMARY")
    mut = c("TEXT_MUTED")
    return (
        f"QMessageBox{{background:{bg};border:1px solid {bd};"
        f"border-radius:14px;font-size:13px;}}"
        f"QMessageBox QLabel{{background:transparent;color:{txt};"
        f"font-size:13px;border:none;}}"
        f"QMessageBox QPushButton{{background:{AMBER};color:#111;"
        f"border:none;border-radius:8px;padding:8px 24px;"
        f"font-size:13px;font-weight:700;min-width:80px;}}"
        f"QMessageBox QPushButton:hover{{background:#FBBF24;}}"
        f"QMessageBox QPushButton:pressed{{background:{ORANGE};color:white;}}"
        f"QMessageBox QPushButton[text='Cancel'],QMessageBox QPushButton[text='No']"
        f"{{background:transparent;color:{mut};border:1.5px solid {bd};}}"
        f"QMessageBox QPushButton[text='Cancel']:hover,"
        f"QMessageBox QPushButton[text='No']:hover"
        f"{{border-color:{AMBER};color:{AMBER};}}"
    )


def build_stylesheet() -> str:
    return f"""
QMainWindow, QWidget {{
    background-color: {c('BG')};
    color: {c('TEXT_PRIMARY')};
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
    font-size: 14px;
}}
QTabWidget::pane {{
    border: 1px solid {c('BORDER')};
    background: {c('PANEL_BG')};
    border-radius: 8px;
}}
QTabBar::tab {{
    background: {c('BG')};
    color: {c('TEXT_MUTED')};
    padding: 10px 24px;
    border: none;
    font-weight: 600;
    font-size: 13px;
}}
QTabBar::tab:selected {{
    background: {c('PANEL_BG')};
    color: {c('ACCENT')};
    border-bottom: 2px solid {c('ACCENT')};
}}
QTabBar::tab:hover:!selected {{ color: {c('TEXT_PRIMARY')}; }}
QTableWidget {{
    background: {c('CARD_BG')};
    border: 1px solid {c('BORDER')};
    border-radius: 6px;
    gridline-color: {c('BORDER')};
    selection-background-color: {c('ACCENT')};
    alternate-background-color: {c('ALT_ROW')};
    color: {c('TEXT_PRIMARY')};
    font-size: 13px;
}}
QTableWidget::item {{ padding: 7px 10px; }}
QHeaderView::section {{
    background: {c('PANEL_BG')};
    color: {c('TEXT_MUTED')};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {c('BORDER')};
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background: {c('INPUT_BG')};
    border: 1.5px solid {c('BORDER')};
    border-radius: 8px;
    padding: 10px 14px;
    color: {c('TEXT_PRIMARY')};
    font-size: 14px;
    min-height: 22px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1.5px solid {c('ACCENT')};
}}
QComboBox {{
    background: {c('INPUT_BG')};
    border: 1.5px solid {c('BORDER')};
    border-radius: 8px;
    padding: 8px 14px;
    color: {c('TEXT_PRIMARY')};
    font-size: 14px;
    min-height: 22px;
}}
QComboBox:focus, QComboBox:on {{
    border: 1.5px solid {c('ACCENT')};
}}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}
QComboBox::down-arrow {{
    image: none; width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c('ACCENT')};
}}
QComboBox QAbstractItemView {{
    background: {c('CARD_BG')};
    border: 1.5px solid {c('BORDER')};
    border-radius: 8px;
    selection-background-color: rgba(245,158,11,0.15);
    color: {c('TEXT_PRIMARY')};
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    min-height: 30px;
}}
QComboBox QAbstractItemView::item:hover {{
    background: rgba(245,158,11,0.10);
    color: {c('ACCENT')};
}}
QPushButton {{
    background: {c('ACCENT')};
    color: #111827;
    border: none;
    border-radius: 8px;
    padding: 10px 22px;
    font-weight: 700;
    font-size: 14px;
}}
QPushButton:hover   {{ background: {c('ACCENT2')}; }}
QPushButton:pressed {{ background: {c('ACCENT3')}; color: #fff; }}
QPushButton[danger="true"]       {{ background: {c('DANGER')}; color: #fff; }}
QPushButton[danger="true"]:hover {{ background: #F87171; }}
QPushButton[secondary="true"] {{
    background: {c('CARD_BG')};
    border: 1.5px solid {c('BORDER')};
    color: {c('TEXT_PRIMARY')};
}}
QPushButton[secondary="true"]:hover {{
    border-color: {c('ACCENT')};
    color: {c('ACCENT')};
}}
QMessageBox {{
    background: {c('CARD_BG')};
}}
QMessageBox QLabel {{
    background: transparent;
    color: {c('TEXT_PRIMARY')};
    font-size: 13px;
}}
QMessageBox QPushButton {{
    background: {c('ACCENT')};
    color: #111;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 700;
    min-width: 80px;
}}
QMessageBox QPushButton:hover {{ background: {c('ACCENT2')}; }}
QGroupBox {{
    border: 1px solid {c('BORDER')};
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px 12px 10px 12px;
    color: {c('TEXT_MUTED')};
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; }}
QLabel[title="true"] {{
    font-size: 22px;
    font-weight: 800;
    color: {c('TEXT_PRIMARY')};
}}
QLabel[subtitle="true"] {{
    font-size: 13px;
    color: {c('TEXT_MUTED')};
}}
QStatusBar {{
    background: {c('PANEL_BG')};
    color: {c('TEXT_MUTED')};
    font-size: 11px;
    border-top: 1px solid {c('BORDER')};
}}
QScrollBar:vertical {{
    background: {c('BG')};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c('SCROLLBAR')};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QFrame[separator="true"] {{
    background: {c('BORDER')};
    max-height: 1px;
}}
"""
