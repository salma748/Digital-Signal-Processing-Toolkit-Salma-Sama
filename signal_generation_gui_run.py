
import tkinter as tk

from gui.signal_generation.window import SignalGenerationWindow


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the temporary root window

    app = SignalGenerationWindow(root, waveform="sine")

    app.mainloop()


if __name__ == "__main__":
    main()
