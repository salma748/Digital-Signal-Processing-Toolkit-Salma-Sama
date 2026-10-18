
import tkinter as tk
from tkinter import messagebox

from core.signal_generator import generate_signal
from gui.plot_panel import PlotPanel

from . import theme
from .widgets import FlatButton, Segmented, StatusBanner


DEFAULTS = {
    "amplitude": "1",
    "phase": "0",
    "frequency": "5",
    "sampling": "50",
    "cycles": "4",
}


class SignalGenerationWindow(tk.Toplevel):
    """GUI for generating and previewing sine and cosine signals."""

    def __init__(self, master, waveform="sine", on_signal=None, on_close=None):
        super().__init__(master)

        self.title("Signal Generation")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=theme.BG)

        self.fonts = theme.Fonts(self)
        theme.apply_styles(self, self.fonts)

        self.on_signal = on_signal
        self.on_close = on_close
        self.current_signal = None
        self.current_sampling_frequency = None

        self.waveform_var = tk.StringVar(
            value="Cosine" if waveform.lower() == "cosine" else "Sine"
        )

        self.amplitude_var = tk.StringVar(value=DEFAULTS["amplitude"])
        self.phase_var = tk.StringVar(value=DEFAULTS["phase"])
        self.frequency_var = tk.StringVar(value=DEFAULTS["frequency"])
        self.sampling_var = tk.StringVar(value=DEFAULTS["sampling"])
        self.cycles_var = tk.StringVar(value=DEFAULTS["cycles"])

        self._build_interface()
        self.frequency_var.trace_add("write", self._update_sampling_hint)

        self._update_sampling_hint()
        self.generate()

    def _build_interface(self):
        outer = tk.Frame(self, bg=theme.BG, padx=16, pady=16)
        outer.pack(fill="both", expand=True)

        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(0, weight=1)

        # Left panel: scrollable controls
        left = tk.Frame(
            outer,
            bg=theme.CARD,
            width=330,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        left.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        left.grid_propagate(False)

        left_canvas = tk.Canvas(
            left,
            bg=theme.CARD,
            highlightthickness=0,
            width=310,
        )

        scrollbar = tk.Scrollbar(
            left,
            orient="vertical",
            command=left_canvas.yview,
        )

        left_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        left_canvas.pack(side="left", fill="both", expand=True)

        controls = tk.Frame(
            left_canvas,
            bg=theme.CARD,
            padx=18,
            pady=18,
        )

        controls_window = left_canvas.create_window(
            (0, 0),
            window=controls,
            anchor="nw",
        )

        def update_scroll_region(_event=None):
            left_canvas.configure(
                scrollregion=left_canvas.bbox("all")
            )

        def resize_controls(event):
            left_canvas.itemconfigure(
                controls_window,
                width=event.width,
            )

        controls.bind("<Configure>", update_scroll_region)
        left_canvas.bind("<Configure>", resize_controls)

        # Enable mouse-wheel scrolling on Windows when hovering over the panel.
        def on_mousewheel(event):
            widget = self.winfo_containing(event.x_root, event.y_root)

            while widget is not None:
                if widget == left_canvas or widget == controls:
                    left_canvas.yview_scroll(
                        int(-1 * (event.delta / 120)),
                        "units",
                    )
                    return
                widget = getattr(widget, "master", None)

        self.bind_all("<MouseWheel>", on_mousewheel)

        self.protocol("WM_DELETE_WINDOW", self.close)

        tk.Label(
            controls,
            text="Signal Generator",
            font=self.fonts.title,
            bg=theme.CARD,
            fg=theme.TEXT,
        ).pack(anchor="w")

        tk.Label(
            controls,
            text="Generate a sinusoidal signal",
            font=self.fonts.small,
            bg=theme.CARD,
            fg=theme.MUTED,
        ).pack(anchor="w", pady=(3, 18))

        self._section(controls, "Waveform")

        Segmented(
            controls,
            ("Sine", "Cosine"),
            self.waveform_var,
            self.fonts.label,
            command=lambda _value: self.generate(),
        ).pack(fill="x", pady=(0, 18))

        self._section(controls, "Parameters")

        self._add_field(controls, "Amplitude (A)", self.amplitude_var)
        self._add_field(
            controls,
            "Phase shift (degrees)",
            self.phase_var,
        )
        self._add_field(
            controls,
            "Analog frequency (Hz)",
            self.frequency_var,
        )
        self._add_field(
            controls,
            "Sampling frequency (Hz)",
            self.sampling_var,
        )

        self.sampling_hint = tk.Label(
            controls,
            text="",
            font=self.fonts.small,
            bg=theme.CARD,
            fg=theme.MUTED,
            anchor="w",
        )
        self.sampling_hint.pack(fill="x", pady=(0, 10))

        self._add_field(
            controls,
            "Number of cycles",
            self.cycles_var,
        )

        buttons = tk.Frame(controls, bg=theme.CARD)
        buttons.pack(fill="x", pady=(12, 0))

        FlatButton(
            buttons,
            "Generate Signal",
            self.generate,
            self.fonts.label,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        FlatButton(
            buttons,
            "Reset",
            self.reset,
            self.fonts.label,
            primary=False,
        ).pack(side="left")

        self.status = StatusBanner(controls, self.fonts.small)
        self.status.pack(fill="x", pady=(14, 10))

        # Signal statistics
        self.statistics = {}

        for label in (
            "Period",
            "Nyquist rate",
            "Number of samples",
            "Sampling ratio",
        ):
            row = tk.Frame(controls, bg=theme.CARD)
            row.pack(fill="x", pady=2)

            tk.Label(
                row,
                text=label,
                font=self.fonts.small,
                bg=theme.CARD,
                fg=theme.MUTED,
            ).pack(side="left")

            value = tk.Label(
                row,
                text="—",
                font=self.fonts.label,
                bg=theme.CARD,
                fg=theme.TEXT,
            )
            value.pack(side="right")

            self.statistics[label] = value

        # Right panel: plot preview
        right = tk.Frame(
            outer,
            bg=theme.CARD,
            highlightthickness=1,
            highlightbackground=theme.BORDER,
        )
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            right,
            text="Signal Preview",
            font=self.fonts.heading,
            bg=theme.CARD,
            fg=theme.TEXT,
        ).pack(anchor="w", padx=16, pady=12)

        self.plot_panel = PlotPanel(right)
        self.plot_panel.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _section(self, parent, text):
        tk.Label(
            parent,
            text=text.upper(),
            font=self.fonts.small,
            bg=theme.CARD,
            fg=theme.MUTED,
        ).pack(anchor="w", pady=(0, 6))

    def _add_field(self, parent, label, variable):
        tk.Label(
            parent,
            text=label,
            font=self.fonts.label,
            bg=theme.CARD,
            fg=theme.TEXT,
        ).pack(anchor="w", pady=(4, 3))

        import tkinter.ttk as ttk

        ttk.Entry(
            parent,
            textvariable=variable,
            style="SG.TEntry",
            font=self.fonts.base,
        ).pack(fill="x", pady=(0, 7))

    def _update_sampling_hint(self, *_):
        try:
            frequency = float(
                self.frequency_var.get().replace(",", ".")
            )

            if frequency > 0:
                self.sampling_hint.config(
                    text=f"Nyquist rate: {2 * frequency:g} Hz"
                )
            else:
                self.sampling_hint.config(
                    text="Frequency must be positive."
                )
        except ValueError:
            self.sampling_hint.config(
                text="Enter a valid analog frequency."
            )

    def generate(self):
        try:
            amplitude = float(
                self.amplitude_var.get().replace(",", ".")
            )
            phase = float(
                self.phase_var.get().replace(",", ".")
            )
            frequency = float(
                self.frequency_var.get().replace(",", ".")
            )
            sampling = float(
                self.sampling_var.get().replace(",", ".")
            )

            cycles_text = self.cycles_var.get().strip()
            cycles = int(cycles_text)

            if not cycles_text or str(cycles) != cycles_text:
                raise ValueError(
                    "Number of cycles must be a whole number."
                )

            signal = generate_signal(
                wave_type=self.waveform_var.get().lower(),
                amplitude=amplitude,
                phase_degrees=phase,
                analog_frequency=frequency,
                sampling_frequency=sampling,
                cycles=cycles,
            )

        except (ValueError, OverflowError) as error:
            self.status.set("error", f"Invalid input: {error}")
            return

        self.current_signal = signal
        self.current_sampling_frequency = sampling

        # Use the existing project plotting component.
        label = f"{self.waveform_var.get()} wave"
        self.plot_panel.show_signals(
            [(label, signal)],
            f"{label} — Discrete Representation",
        )

        period = 1 / frequency
        nyquist_rate = 2 * frequency
        number_of_samples = len(signal.samples)

        self.statistics["Period"].config(
            text=f"{period:.4g} s"
        )
        self.statistics["Nyquist rate"].config(
            text=f"{nyquist_rate:g} Hz"
        )
        self.statistics["Number of samples"].config(
            text=f"{number_of_samples:,}"
        )
        self.statistics["Sampling ratio"].config(
            text=f"{sampling / frequency:.2f}"
        )

        self.status.set(
            "ok",
            f"Generated {number_of_samples} samples successfully.",
        )

        # Optional integration point for the main application.
        if self.on_signal is not None:
            self.on_signal(signal)

    def reset(self):
        self.amplitude_var.set(DEFAULTS["amplitude"])
        self.phase_var.set(DEFAULTS["phase"])
        self.frequency_var.set(DEFAULTS["frequency"])
        self.sampling_var.set(DEFAULTS["sampling"])
        self.cycles_var.set(DEFAULTS["cycles"])
        self.waveform_var.set("Sine")

        self.generate()

    def close(self):
        self.unbind_all("<MouseWheel>")
        self.destroy()
        if self.on_close is not None:
            self.on_close()
