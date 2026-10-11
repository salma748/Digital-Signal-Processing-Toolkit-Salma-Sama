from dataclasses import dataclass

@dataclass
class Signal:
    samples: dict[int, float]