import tkinter as tk
from tkinter import messagebox, ttk

from gui.main_window import MainWindow
from gui.signal_generation.window import SignalGenerationWindow
from gui.signal_quantization_window import SignalQuantizationWindow


class TaskMenu:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Digital Signal Processing Toolkit")
        root.geometry("480x300")
        root.minsize(420, 260)

        frame = ttk.Frame(root, padding=24)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Digital Signal Processing Toolkit",
            font=("Helvetica", 16, "bold"),
        ).pack(anchor="w", pady=(0, 18))

        tasks = (
            ("Task 1 : Signal Operations", self._open_task1),
            ("Task 2 : Signal Generation", self._open_task2),
            ("Task 3 : Signal Quantization", self._open_task3),
        )
        for text, command in tasks:
            ttk.Button(frame, text=text, command=command).pack(
                fill=tk.X, pady=5, ipady=5
            )

    def _launch(self, create_window):
        existing_windows = {
            child
            for child in self.root.winfo_children()
            if isinstance(child, tk.Toplevel)
        }
        self.root.withdraw()
        try:
            return create_window()
        except Exception as error:
            for child in self.root.winfo_children():
                if isinstance(child, tk.Toplevel) and child not in existing_windows:
                    child.destroy()
            self.root.deiconify()
            messagebox.showerror(
                "Could not open task",
                f"The task window could not be opened:\n{error}",
                parent=self.root,
            )
            return None

    def _open_task1(self):
        def create_window():
            window = tk.Toplevel(self.root)
            window.protocol("WM_DELETE_WINDOW", lambda: self._close_task(window))
            MainWindow(window)
            return window

        self._launch(create_window)

    def _open_task2(self):
        self._launch(
            lambda: SignalGenerationWindow(self.root, on_close=self._show_menu)
        )

    def _open_task3(self):
        self._launch(
            lambda: SignalQuantizationWindow(self.root, on_close=self._show_menu)
        )

    def _close_task(self, window: tk.Toplevel):
        window.destroy()
        self._show_menu()

    def _show_menu(self):
        if self.root.winfo_exists():
            self.root.deiconify()
            self.root.lift()
