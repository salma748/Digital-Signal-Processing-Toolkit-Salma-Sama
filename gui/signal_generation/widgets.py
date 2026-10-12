from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Sequence

from . import theme


class FlatButton(tk.Label):
    def __init__(self, master, text: str, command: Callable[[], None], font,
                 primary: bool = True, **kw):
        self._bg = theme.ACCENT if primary else theme.CARD
        self._hover = theme.ACCENT_HOVER if primary else theme.SECONDARY_HOVER
        self._fg = "#FFFFFF" if primary else theme.TEXT
        super().__init__(master, text=text, font=font, bg=self._bg, fg=self._fg,
                         padx=16, pady=9, cursor="hand2",
                         highlightthickness=0 if primary else 1,
                         highlightbackground=theme.BORDER, **kw)
        self._command = command
        self.bind("<Enter>", lambda _e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda _e: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda _e: self._command())


class Segmented(tk.Frame):
    """Pill-style single-choice selector bound to a tk.StringVar."""

    def __init__(self, master, options: Sequence[str], variable: tk.StringVar, font,
                 command: Optional[Callable[[str], None]] = None, bg: str = theme.CARD):
        super().__init__(master, bg=theme.ACCENT_SOFT, padx=3, pady=3)
        self._var, self._command, self._buttons = variable, command, {}
        for opt in options:
            lbl = tk.Label(self, text=opt, font=font, padx=14, pady=6, cursor="hand2")
            lbl.pack(side="left", expand=True, fill="x")
            lbl.bind("<Button-1>", lambda _e, o=opt: self.select(o))
            self._buttons[opt] = lbl
        self.refresh()

    def select(self, option: str) -> None:
        changed = self._var.get() != option
        self._var.set(option)
        self.refresh()
        if changed and self._command:
            self._command(option)

    def refresh(self) -> None:
        current = self._var.get()
        for opt, lbl in self._buttons.items():
            active = opt == current
            lbl.config(bg=theme.ACCENT if active else theme.ACCENT_SOFT,
                       fg="#FFFFFF" if active else theme.ACCENT)


class StatusBanner(tk.Label):
    """Coloured message box: info / ok / warn / error."""

    _STYLES = {"info": (theme.INFO_BG, theme.INFO_FG), "ok": (theme.OK_BG, theme.OK_FG),
               "warn": (theme.WARN_BG, theme.WARN_FG), "error": (theme.ERR_BG, theme.ERR_FG)}

    def __init__(self, master, font):
        super().__init__(master, font=font, anchor="w", justify="left", padx=12, pady=10)
        self.set("info", "Enter the parameters and press Generate.")

    def set(self, kind: str, message: str) -> None:
        bg, fg = self._STYLES[kind]
        self.config(bg=bg, fg=fg, text=message, wraplength=self.winfo_width() - 24
                    if self.winfo_width() > 60 else 290)
