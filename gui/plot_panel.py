import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from core.signal_plotter import draw_signals
from models.signal import Signal


class PlotPanel(ttk.LabelFrame):

    def __init__(self, parent):
        super().__init__(parent, text=" Signal plot ", padding=6)

        self.figure = Figure(figsize=(7, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)

        toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.show_message("Load a signal, then plot it or choose an operation.")

    def show_message(self, text: str):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.axis("off")
        ax.text(0.5, 0.5, text, ha="center", va="center", fontsize=12, color="gray")
        self.canvas.draw()

    def show_signals(self, labeled_signals: list[tuple[str, Signal]], title: str):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        draw_signals(ax, labeled_signals, title)
        self._redraw()

    def show_operation(self, inputs: list[tuple[str, Signal]], result: Signal, result_title: str):
        self.figure.clear()
        top, bottom = self.figure.subplots(2, 1, sharex=True)
        draw_signals(top, inputs, "Input signal" if len(inputs) == 1 else "Input signals")
        draw_signals(bottom, [(result_title, result)], f"Result: {result_title}")
        self._redraw()

    def _redraw(self):
        self.figure.tight_layout()
        self.canvas.draw()