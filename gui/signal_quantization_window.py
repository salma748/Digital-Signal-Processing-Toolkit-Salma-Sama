import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core.input_signal import read_signal_from_file
from core.signal_quantizer import quantize_signal
from gui.plot_panel import PlotPanel
from models.signal import Signal


class SignalQuantizationWindow(tk.Toplevel):
    def __init__(self, master, on_close=None):
        super().__init__(master)
        self.title("Task 3: Signal Quantization")
        self.geometry("1150x720")
        self.minsize(920, 600)
        self.protocol("WM_DELETE_WINDOW", self._close)

        self.on_close = on_close
        self.signal: Signal | None = None
        self.signal_name = ""
        self.mode_var = tk.StringVar(value="bits")
        self.status_var = tk.StringVar(value="Load a signal to begin.")

        self._build_interface()

    def _build_interface(self):
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(
            header,
            text="Task 3 : Signal Quantization",
            font=("Helvetica", 15, "bold"),
        ).pack(side=tk.LEFT)
        ttk.Button(header, text="Main Menu", command=self._close).pack(side=tk.RIGHT)

        controls = ttk.LabelFrame(outer, text="Quantization settings", padding=8)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(5, weight=1)

        ttk.Button(controls, text="Load signal...", command=self._load_signal).grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.signal_label = ttk.Label(controls, text="No signal loaded")
        self.signal_label.grid(row=0, column=1, columnspan=5, sticky="w")

        ttk.Label(controls, text="Quantization input:").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Radiobutton(
            controls,
            text="Number of bits",
            variable=self.mode_var,
            value="bits",
            command=self._update_value_label,
        ).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Radiobutton(
            controls,
            text="Number of levels",
            variable=self.mode_var,
            value="levels",
            command=self._update_value_label,
        ).grid(row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0))
        self.value_label = ttk.Label(controls, text="Bits:")
        self.value_label.grid(row=1, column=3, sticky="e", padx=(12, 4), pady=(8, 0))
        self.value_entry = ttk.Entry(controls, width=10)
        self.value_entry.insert(0, "3")
        self.value_entry.grid(row=1, column=4, sticky="w", pady=(8, 0))
        ttk.Button(controls, text="Quantize", command=self._quantize).grid(
            row=1, column=5, sticky="e", padx=(12, 0), pady=(8, 0)
        )

        body = ttk.Frame(outer)
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1, minsize=440)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)

        results = ttk.LabelFrame(body, text="Quantization results", padding=6)
        results.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        results.rowconfigure(0, weight=1)
        results.columnconfigure(0, weight=1)

        columns = ("sample_index", "input", "interval", "encoded", "quantized", "error")
        self.results_tree = ttk.Treeview(
            results, columns=columns, show="headings", height=18
        )
        headings = (
            ("sample_index", "Index", 55),
            ("input", "Input", 80),
            ("interval", "Interval", 65),
            ("encoded", "Encoded", 72),
            ("quantized", "Quantized", 85),
            ("error", "Error", 80),
        )
        for column, title, width in headings:
            self.results_tree.heading(column, text=title)
            self.results_tree.column(column, width=width, minwidth=45, anchor=tk.CENTER)
        vertical_scroll = ttk.Scrollbar(
            results, orient=tk.VERTICAL, command=self.results_tree.yview
        )
        horizontal_scroll = ttk.Scrollbar(
            results, orient=tk.HORIZONTAL, command=self.results_tree.xview
        )
        self.results_tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        self.plot_panel = PlotPanel(body)
        self.plot_panel.grid(row=0, column=1, sticky="nsew")

        ttk.Label(outer, textvariable=self.status_var, relief=tk.SUNKEN, padding=4).grid(
            row=3, column=0, sticky="ew", pady=(8, 0)
        )

    def _update_value_label(self):
        self.value_label.config(
            text="Bits:" if self.mode_var.get() == "bits" else "Levels:"
        )

    def _load_signal(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Select a signal file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            self.status_var.set("Signal loading cancelled.")
            return

        try:
            signal = read_signal_from_file(path)
        except (OSError, ValueError) as error:
            self.status_var.set("Could not load signal.")
            messagebox.showerror("Could not load signal", str(error), parent=self)
            return

        self.signal = signal
        self.signal_name = os.path.basename(path)
        self.signal_label.config(
            text=f"{self.signal_name} ({len(signal.samples)} samples)"
        )
        self._clear_results()
        self.status_var.set(f"Loaded {self.signal_name}.")

    def _quantize(self):
        if self.signal is None:
            self._show_validation_error("Load a signal file before quantizing.")
            return

        raw_value = self.value_entry.get().strip()
        try:
            if not raw_value:
                raise ValueError("Enter a positive whole number.")
            value = int(raw_value)
            if self.mode_var.get() == "bits":
                result = quantize_signal(self.signal, bits=value)
            else:
                result = quantize_signal(self.signal, levels=value)
        except (ValueError, TypeError) as error:
            self._show_validation_error(str(error))
            return

        self._clear_results()
        for (sample_index, input_value), interval, encoded in zip(
            self.signal.samples.items(),
            result.interval_indices,
            result.encoded_values,
        ):
            self.results_tree.insert(
                "",
                tk.END,
                values=(
                    sample_index,
                    f"{input_value:.6g}",
                    interval,
                    encoded,
                    f"{result.quantized_signal.samples[sample_index]:.6g}",
                    f"{result.quantization_error.samples[sample_index]:.6g}",
                ),
            )

        if self.signal.samples:
            self.plot_panel.show_signals(
                [
                    (self.signal_name or "Original signal", self.signal),
                    ("Quantized signal", result.quantized_signal),
                ],
                "Original and quantized signals",
            )
        else:
            self.plot_panel.show_message("The loaded signal has no samples.")

        mode = "bits" if self.mode_var.get() == "bits" else "levels"
        self.status_var.set(
            f"Quantized {len(self.signal.samples)} samples using {value} {mode}."
        )

    def _clear_results(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.plot_panel.show_message("Load a signal and run quantization to see results.")

    def _show_validation_error(self, message):
        self.status_var.set(message)
        messagebox.showerror("Invalid quantization input", message, parent=self)

    def _close(self):
        self.destroy()
        if self.on_close is not None:
            self.on_close()