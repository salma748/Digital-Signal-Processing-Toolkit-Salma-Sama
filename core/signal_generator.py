
import math
from models.signal import Signal


def generate_signal(
    wave_type: str,
    amplitude: float,
    phase_degrees: float,
    analog_frequency: float,
    sampling_frequency: float,
    cycles: int = 1
) -> Signal:
   

    if amplitude < 0:
        raise ValueError("Amplitude cannot be negative.")

    if analog_frequency <= 0:
        raise ValueError("Analog frequency must be positive.")

    if sampling_frequency <= 0:
        raise ValueError("Sampling frequency must be positive.")

    if sampling_frequency < 2 * analog_frequency:
        raise ValueError(
            "Sampling frequency must be at least twice "
            "the analog frequency."
        )

    if cycles < 1:
        raise ValueError("Number of cycles must be at least 1.")

    wave_type = wave_type.lower()

    if wave_type not in ("sine", "cosine"):
        raise ValueError("Wave type must be sine or cosine.")

   
    phase = math.radians(phase_degrees)

    
    number_of_samples = math.ceil(
        cycles * sampling_frequency / analog_frequency
    )

    
    samples = {}

    for n in range(number_of_samples):
        time = n / sampling_frequency
        angle = 2 * math.pi * analog_frequency * time + phase

        if wave_type == "sine":
            value = amplitude * math.sin(angle)
        else:
            value = amplitude * math.cos(angle)

        samples[n] = value

    
    return Signal(samples=samples)
