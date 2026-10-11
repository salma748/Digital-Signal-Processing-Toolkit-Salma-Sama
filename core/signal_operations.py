from models.signal import Signal


def multiply_signal(signal: Signal, constant: float) -> Signal:

    result = {}

    for index, value in signal.samples.items():
        result[index] = value * constant

    return Signal(result)

def add_signals(signals: list[Signal]) -> Signal:

    result = {}

    for signal in signals:
        for index, value in signal.samples.items():
            result[index] = result.get(index, 0) + value

    return Signal(result)

def subtract_signals(signal1: Signal, signal2: Signal) -> Signal:
   
    negative_signal2 = multiply_signal(signal2, -1)

    return add_signals([signal1, negative_signal2])   

def shift_signal(signal: Signal, k: int) -> Signal:

    result = {}

    for index, value in signal.samples.items():
        new_index = index + k
        result[new_index] = value

    return Signal(result)

def delay_signal(signal: Signal, k: int) -> Signal:

    if k < 0:
        raise ValueError("k must be 0 or more for a delay.")

    return shift_signal(signal, k)

def advance_signal(signal: Signal, k: int) -> Signal:

    if k < 0:
        raise ValueError("k must be 0 or more for an advance.")

    return shift_signal(signal, -k)

def fold_signal(signal: Signal) -> Signal:
    
    result = {}

    for index, value in signal.samples.items():
        result[-index] = value

    return Signal(result)