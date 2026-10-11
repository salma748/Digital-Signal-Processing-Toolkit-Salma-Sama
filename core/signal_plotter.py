from matplotlib.ticker import MaxNLocator

from models.signal import Signal


def draw_signals(ax, labeled_signals: list[tuple[str, Signal]], title: str):

    for position, (label, signal) in enumerate(labeled_signals):
        color = f"C{position % 10}"
        sorted_samples = sorted(signal.samples.items())

        indices = [index for index, value in sorted_samples]
        values = [value for index, value in sorted_samples]

        ax.stem(indices, values, linefmt=f"{color}-", markerfmt=f"{color}o",
                basefmt="k-", label=label)

    ax.set_xlabel("Sample index (n)")
    ax.set_ylabel("Amplitude")
    ax.set_title(title)
    ax.grid(True)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    if len(labeled_signals) > 1:
        ax.legend(fontsize=8)


def plot_signal(signal: Signal, title: str = "Signal"):

    import matplotlib.pyplot as plt

    figure, ax = plt.subplots()
    draw_signals(ax, [("x[n]", signal)], title)
    plt.show()