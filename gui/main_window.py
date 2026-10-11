from __future__ import annotations

import math
import os
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk

from core.input_signal import read_signal_from_file
from core.signal_operations import (
    add_signals,
    advance_signal,
    delay_signal,
    fold_signal,
    multiply_signal,
    subtract_signals,
)
from gui.plot_panel import PlotPanel
from models.signal import Signal


class InputError(Exception):
    pass


@dataclass
class LoadedSignal:
    number: int
    name: str
    signal: Signal

    @property
    def tag(self) -> str:
        return f"S{self.number}"

    @property
    def label(self) -> str:
        return f"{self.tag}: {self.name}"

    @property
    def list_text(self) -> str:
        return f"{self.label}  ({len(self.signal.samples)} samples)"


def parse_float(text: str, field: str) -> float:
    try:
        value = float(text.strip())
    except ValueError:
        raise InputError(f"{field} must be a number (for example 5 or -0.5).\nYou entered: '{text}'")
    if not math.isfinite(value):
        raise InputError(f"{field} must be a normal finite number.")
    return value


def parse_int(text: str, field: str) -> int:
    try:
        return int(text.strip())
    except ValueError:
        raise InputError(f"{field} must be a whole number (for example 3).\nYou entered: '{text}'")


class MainWindow:
    PAD = 8

    def __init__(self, root: tk.Tk):
        self.root = root
        self.signals: list[LoadedSignal] = []
        self.next_number = 1
        self.pending_result: tuple[str, Signal] | None = None
        self.signal_combos: list[ttk.Combobox] = []

        root.title("DSP Toolkit - Task 1: Basic Signal Operations")
        root.geometry("1200x720")
        root.minsize(1000, 640)

        self.status_var = tk.StringVar()
        self._build_header()
        self._build_status_bar()
        self._build_body()
        self._refresh_signal_views()
        self._set_status("Ready. Click 'Load signal(s)...' to begin.")

    def _build_header(self):
        header = ttk.Frame(self.root, padding=(12, 8))
        header.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(header, text="Digital Signal Processing",
                  font=("Helvetica", 16, "bold")).pack(anchor="w")
        ttk.Label(header, text="Task 1",
                  foreground="gray30").pack(anchor="w")
        ttk.Separator(self.root).pack(side=tk.TOP, fill=tk.X)

    def _build_status_bar(self):
        bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(8, 3))
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(bar, textvariable=self.status_var).pack(side=tk.LEFT)

    def _build_body(self):
        body = ttk.Frame(self.root, padding=self.PAD)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self.PAD))
        right = ttk.Frame(body)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_signal_list(left)
        self._build_operations(left)

        self._build_result_bar(right)
        self.plot_panel = PlotPanel(right)
        self.plot_panel.pack(fill=tk.BOTH, expand=True)

    def _build_signal_list(self, parent):
        box = ttk.LabelFrame(parent, text=" 1. Loaded signals ", padding=self.PAD)
        box.pack(fill=tk.X)

        list_frame = ttk.Frame(box)
        list_frame.pack(fill=tk.X)
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=7, width=46,
                                  exportselection=False, activestyle="none")
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(box, text="Tip: Ctrl+click or Shift+click to select several signals.",
                  foreground="gray30").pack(anchor="w", pady=(4, 6))

        buttons = ttk.Frame(box)
        buttons.pack(fill=tk.X)
        buttons.columnconfigure((0, 1), weight=1)
        actions = [
            ("Load signal(s)...", self.on_load),
            ("Plot selected", self.on_plot_selected),
            ("Remove selected", self.on_remove),
            ("Clear all", self.on_clear),
        ]
        for i, (text, command) in enumerate(actions):
            ttk.Button(buttons, text=text, command=lambda c=command: self._safe(c)).grid(
                row=i // 2, column=i % 2, sticky="ew", padx=2, pady=2)

    def _build_operations(self, parent):
        box = ttk.LabelFrame(parent, text=" 2. Operations ", padding=self.PAD)
        box.pack(fill=tk.X, pady=(self.PAD, 0))
        notebook = ttk.Notebook(box)
        notebook.pack(fill=tk.X)

        self._build_add_tab(notebook)
        self._build_subtract_tab(notebook)
        self._build_multiply_tab(notebook)
        self._build_shift_tab(notebook)
        self._build_fold_tab(notebook)

    def _build_result_bar(self, parent):
        bar = ttk.LabelFrame(parent, text=" 3. Result ", padding=self.PAD)
        bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(self.PAD, 0))
        self.result_label = ttk.Label(bar, text="No result yet.")
        self.result_label.pack(side=tk.LEFT)
        self.keep_button = ttk.Button(bar, text="Keep result as new signal", state=tk.DISABLED,
                                      command=lambda: self._safe(self.on_keep_result))
        self.keep_button.pack(side=tk.RIGHT)

    def _new_tab(self, notebook, title, description):
        tab = ttk.Frame(notebook, padding=self.PAD)
        notebook.add(tab, text=title)
        tab.columnconfigure(1, weight=1)
        ttk.Label(tab, text=description, wraplength=380, justify=tk.LEFT,
                  foreground="gray30").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        return tab

    def _add_combo(self, tab, row, text):
        ttk.Label(tab, text=text).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=3)
        combo = ttk.Combobox(tab, state="readonly", width=34)
        combo.grid(row=row, column=1, sticky="ew", pady=3)
        self.signal_combos.append(combo)
        return combo

    def _add_entry(self, tab, row, text, default):
        ttk.Label(tab, text=text).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=3)
        entry = ttk.Entry(tab, width=12)
        entry.insert(0, default)
        entry.grid(row=row, column=1, sticky="w", pady=3)
        return entry

    def _add_run_button(self, tab, row, text, command):
        ttk.Button(tab, text=text, command=lambda: self._safe(command)).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _build_add_tab(self, notebook):
        tab = self._new_tab(notebook, "Add",
                            "Adds ALL signals selected in the 'Loaded signals' list "
                            "(select 2 or more). A missing index counts as 0.")
        self._add_run_button(tab, 1, "Add selected signals", self.on_add)

    def _build_subtract_tab(self, notebook):
        tab = self._new_tab(notebook, "Subtract", "Computes  A - B  and shows the result.")
        self.subtract_a = self._add_combo(tab, 1, "Signal A:")
        self.subtract_b = self._add_combo(tab, 2, "Signal B:")
        self._add_run_button(tab, 3, "Compute A - B", self.on_subtract)

    def _build_multiply_tab(self, notebook):
        tab = self._new_tab(notebook, "Multiply",
                            "Multiplies every sample by a constant (amplify or reduce).")
        self.multiply_combo = self._add_combo(tab, 1, "Signal:")
        self.constant_entry = self._add_entry(tab, 2, "Constant:", "2")
        self._add_run_button(tab, 3, "Multiply by constant", self.on_multiply)

    def _build_shift_tab(self, notebook):
        tab = self._new_tab(notebook, "Delay / Advance",
                            "k = number of steps (whole number, 0 or more).\n"
                            "Delay x(n-k) moves the signal RIGHT.  Advance x(n+k) moves it LEFT.")
        self.shift_combo = self._add_combo(tab, 1, "Signal:")
        self.shift_entry = self._add_entry(tab, 2, "k:", "1")
        self.shift_mode = tk.StringVar(value="delay")
        mode_frame = ttk.Frame(tab)
        mode_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=3)
        ttk.Radiobutton(mode_frame, text="Delay  x(n - k)", variable=self.shift_mode,
                        value="delay").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(mode_frame, text="Advance  x(n + k)", variable=self.shift_mode,
                        value="advance").pack(side=tk.LEFT)
        self._add_run_button(tab, 4, "Apply shift", self.on_shift)

    def _build_fold_tab(self, notebook):
        tab = self._new_tab(notebook, "Fold", "Reverses the signal: x(n) becomes x(-n).")
        self.fold_combo = self._add_combo(tab, 1, "Signal:")
        self._add_run_button(tab, 2, "Fold signal", self.on_fold)

    def on_load(self):
        paths = filedialog.askopenfilenames(
            title="Select signal file(s)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not paths:
            self._set_status("Loading cancelled.")
            return

        loaded_count, errors = 0, []
        for path in paths:
            file_name = os.path.basename(path)
            try:
                signal = read_signal_from_file(path)
            except (ValueError, OSError) as error:
                errors.append(f"{file_name}: {error}")
                continue
            self._add_signal(file_name, signal)
            loaded_count += 1

        self._refresh_signal_views()
        if errors:
            messagebox.showerror(
                "Could not load some files",
                "\n\n".join(errors) + "\n\nExpected format: first line = N, "
                "then N lines of 'index value'.")
        self._set_status(f"Loaded {loaded_count} signal(s)." +
                         (f" {len(errors)} file(s) failed." if errors else ""))

    def on_plot_selected(self):
        selected = self._selected_signals(minimum=1)
        title = selected[0].label if len(selected) == 1 else "Selected signals"
        self.plot_panel.show_signals([(s.label, s.signal) for s in selected], title)
        self._set_status(f"Plotted: {', '.join(s.tag for s in selected)}.")

    def on_remove(self):
        selected = self._selected_signals(minimum=1)
        removed = {s.number for s in selected}
        self.signals = [s for s in self.signals if s.number not in removed]
        self._refresh_signal_views()
        self._set_status(f"Removed {len(removed)} signal(s).")

    def on_clear(self):
        if not self.signals:
            raise InputError("There are no signals to clear.")
        if messagebox.askyesno("Clear all", "Remove all loaded signals?"):
            self.signals.clear()
            self.pending_result = None
            self.keep_button.config(state=tk.DISABLED)
            self._refresh_signal_views()
            self.plot_panel.show_message("Load a signal, then plot it or choose an operation.")
            self.result_label.config(text="No result yet.")
            self._set_status("All signals removed.")

    def on_add(self):
        selected = self._selected_signals(minimum=2)
        result = add_signals([s.signal for s in selected])
        name = "Add " + " + ".join(s.tag for s in selected)
        self._show_result(selected, result, name)

    def on_subtract(self):
        a = self._combo_signal(self.subtract_a, "Signal A")
        b = self._combo_signal(self.subtract_b, "Signal B")
        result = subtract_signals(a.signal, b.signal)
        self._show_result([a, b], result, f"Subtract {a.tag} - {b.tag}")

    def on_multiply(self):
        item = self._combo_signal(self.multiply_combo, "a signal")
        constant = parse_float(self.constant_entry.get(), "Constant")
        result = multiply_signal(item.signal, constant)
        self._show_result([item], result, f"{item.tag} * {constant:g}")

    def on_shift(self):
        item = self._combo_signal(self.shift_combo, "a signal")
        k = parse_int(self.shift_entry.get(), "k")
        if k < 0:
            raise InputError("k must be 0 or more. Use Delay / Advance to choose the direction.")
        if self.shift_mode.get() == "delay":
            result = delay_signal(item.signal, k)
            name = f"Delay {item.tag} by {k}"
        else:
            result = advance_signal(item.signal, k)
            name = f"Advance {item.tag} by {k}"
        self._show_result([item], result, name)

    def on_fold(self):
        item = self._combo_signal(self.fold_combo, "a signal")
        result = fold_signal(item.signal)
        self._show_result([item], result, f"Fold {item.tag}")

    def on_keep_result(self):
        if self.pending_result is None:
            raise InputError("There is no result to keep yet.")
        name, signal = self.pending_result
        item = self._add_signal(name, signal)
        self.pending_result = None
        self.keep_button.config(state=tk.DISABLED)
        self._refresh_signal_views()
        self._set_status(f"Result saved as {item.tag}. You can use it in other operations now.")

    def _add_signal(self, name: str, signal: Signal) -> LoadedSignal:
        item = LoadedSignal(self.next_number, name, signal)
        self.next_number += 1
        self.signals.append(item)
        return item

    def _selected_signals(self, minimum: int) -> list[LoadedSignal]:
        if not self.signals:
            raise InputError("No signals loaded yet. Click 'Load signal(s)...' first.")
        indices = self.listbox.curselection()
        if len(indices) < minimum:
            raise InputError(f"Select at least {minimum} signal(s) in the 'Loaded signals' list first.")
        return [self.signals[i] for i in indices]

    def _combo_signal(self, combo: ttk.Combobox, what: str) -> LoadedSignal:
        if not self.signals:
            raise InputError("No signals loaded yet. Click 'Load signal(s)...' first.")
        index = combo.current()
        if index < 0:
            raise InputError(f"Please choose {what}.")
        return self.signals[index]

    def _show_result(self, inputs: list[LoadedSignal], result: Signal, name: str):
        self.pending_result = (name, result)
        self.keep_button.config(state=tk.NORMAL)
        self.result_label.config(text=f"Showing: {name}  ({len(result.samples)} samples)")
        self.plot_panel.show_operation([(s.label, s.signal) for s in inputs], result, name)
        self._set_status(f"{name} done. Use 'Keep result' to reuse it in more operations.")

    def _refresh_signal_views(self):
        texts = [s.list_text for s in self.signals]
        self.listbox.delete(0, tk.END)
        for text in texts:
            self.listbox.insert(tk.END, text)
        for combo in self.signal_combos:
            previous = combo.current()
            combo["values"] = texts
            if texts:
                combo.current(previous if 0 <= previous < len(texts) else 0)
            else:
                combo.set("")

    def _safe(self, action):
        try:
            action()
        except InputError as error:
            self._show_error("Invalid input", str(error))
        except Exception as error:
            self._show_error("Unexpected error", f"Something went wrong:\n{error}")

    def _show_error(self, title: str, message: str):
        messagebox.showerror(title, message)
        self._set_status("Last action failed. See the error message.")

    def _set_status(self, text: str):
        self.status_var.set(text)