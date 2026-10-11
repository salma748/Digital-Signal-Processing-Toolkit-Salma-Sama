from models.signal import Signal


def read_signal_from_file(file_path: str) -> Signal:

    with open(file_path, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    if not lines:
        raise ValueError("The signal file is empty.")

    number_of_samples = int(lines[0])

    sample_lines = lines[1:]

    if len(sample_lines) != number_of_samples:
        raise ValueError(
            f"Expected {number_of_samples} samples, "
            f"but found {len(sample_lines)}."
        )

    samples = {}

    for line in sample_lines:
        parts = line.split()

        if len(parts) != 2:
            raise ValueError(
                f"Each sample must contain an index and a value. "
                f"Invalid line: {line}"
            )

        index = int(parts[0])
        value = float(parts[1])

        samples[index] = value

    return Signal(samples)