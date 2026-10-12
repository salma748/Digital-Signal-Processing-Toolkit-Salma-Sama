
from __future__ import annotations

from tkinter import font as tkfont
from tkinter import ttk


# Window and component colors
BG = "#F3F5F9"
CARD = "#FFFFFF"
BORDER = "#DDE2EC"
TEXT = "#1F2937"
MUTED = "#6B7280"

# Primary accent colors
ACCENT = "#4F46E5"
ACCENT_HOVER = "#4338CA"
ACCENT_SOFT = "#EEF0FF"
SECONDARY_HOVER = "#E8EBF3"

# Status colors
OK_BG = "#E7F7EE"
OK_FG = "#157347"

WARN_BG = "#FFF4DB"
WARN_FG = "#8A5A00"

ERR_BG = "#FDE8E8"
ERR_FG = "#B42318"

INFO_BG = ACCENT_SOFT
INFO_FG = ACCENT

# Plot colors: useful when displaying multiple signals
SIGNAL_COLORS = [
    "#4F46E5",
    "#E8590C",
    "#0E9F6E",
    "#C026D3",
]

GRID = "#E5E7EB"

# Preferred fonts, in order of preference
_PREFERRED = (
    "Segoe UI",
    "SF Pro Text",
    "Helvetica Neue",
    "Inter",
    "Ubuntu",
    "DejaVu Sans",
)


def pick_font_family(root) -> str:
    """Choose the first preferred font available on the system."""
    available = set(tkfont.families(root))

    for name in _PREFERRED:
        if name in available:
            return name

    return "TkDefaultFont"


class Fonts:
    """Centralized font definitions for the Signal Generation GUI."""

    def __init__(self, root):
        family = pick_font_family(root)

        available = set(tkfont.families(root))

        self.base = (family, 10)
        self.small = (family, 9)
        self.label = (family, 10, "bold")
        self.title = (family, 17, "bold")
        self.heading = (family, 12, "bold")

        mono_family = "Consolas" if "Consolas" in available else "Courier"
        self.mono = (mono_family, 10)


def apply_styles(root, fonts: Fonts) -> None:
    """Configure ttk styles for the Signal Generation interface."""

    style = ttk.Style(root)

    style.configure(
        "SG.TFrame",
        background=BG,
    )

    style.configure(
        "SG.Card.TFrame",
        background=CARD,
    )

    style.configure(
        "SG.TLabel",
        background=CARD,
        foreground=TEXT,
        font=fonts.base,
    )

    style.configure(
        "SG.TEntry",
        padding=6,
        fieldbackground=CARD,
        foreground=TEXT,
    )

    style.configure(
        "SG.TCombobox",
        padding=5,
        fieldbackground=CARD,
        foreground=TEXT,
    )

    style.configure(
        "SG.TSeparator",
        background=BORDER,
    )
