import math
from dataclasses import dataclass

from models.signal import Signal


@dataclass(frozen=True)
class QuantizationResult:
	interval_indices: list[int]
	encoded_values: list[str]
	quantized_signal: Signal
	quantization_error: Signal


def quantize_signal(
	signal: Signal,
	*,
	bits: int | None = None,
	levels: int | None = None,
) -> QuantizationResult:
	"""Uniformly quantize samples using either a bit count or level count.

	The range is the signal's minimum-to-maximum value, split into equal-width
	intervals. Samples reconstruct to interval midpoints; error is reconstructed
	minus original. Interval labels are one-based and the maximum maps
	to the final interval. Encoded values are zero-padded binary strings for
	the corresponding zero-based level. A constant signal reconstructs exactly
	to its value in interval one.

	Output lists follow the sample dictionary's iteration order. Quantized and
	error outputs are Signals, so their original sample indices are retained.
	"""
	if not isinstance(signal, Signal):
		raise TypeError("signal must be a Signal instance.")
	if (bits is None) == (levels is None):
		raise ValueError("Supply exactly one of bits or levels.")

	if bits is not None:
		_validate_count(bits, "bits")
		quantization_levels = 1 << bits
		encoding_width = bits
	else:
		_validate_count(levels, "levels")
		quantization_levels = levels
		encoding_width = max(1, (levels - 1).bit_length())

	sample_items = list(signal.samples.items())
	values = [value for _, value in sample_items]
	for value in values:
		try:
			is_finite = math.isfinite(value)
		except TypeError as error:
			raise ValueError("Signal samples must be finite numbers.") from error
		if not is_finite:
			raise ValueError("Signal samples must be finite numbers.")

	if not sample_items:
		return QuantizationResult([], [], Signal({}), Signal({}))

	minimum = min(values)
	maximum = max(values)
	span = maximum - minimum
	interval_indices = []
	encoded_values = []
	quantized_samples = {}
	error_samples = {}

	for sample_index, value in sample_items:
		if minimum == maximum:
			level_index = 0
			quantized_value = value
		else:
			if math.isfinite(span):
				position = (value - minimum) / span
			else:
				scale = max(abs(minimum), abs(maximum))
				scaled_minimum = minimum / scale
				position = (value / scale - scaled_minimum) / (
					maximum / scale - scaled_minimum
				)

			# Clamping also puts the inclusive maximum in the final interval.
			level_index = min(
				quantization_levels - 1,
				max(0, int(position * quantization_levels)),
			)
			midpoint_fraction = (level_index + 0.5) / quantization_levels
			quantized_value = (
				minimum * (1 - midpoint_fraction)
				+ maximum * midpoint_fraction
			)

		interval_indices.append(level_index + 1)
		encoded_values.append(format(level_index, f"0{encoding_width}b"))
		quantized_samples[sample_index] = quantized_value
		error_samples[sample_index] = quantized_value - value

	return QuantizationResult(
		interval_indices=interval_indices,
		encoded_values=encoded_values,
		quantized_signal=Signal(quantized_samples),
		quantization_error=Signal(error_samples),
	)


def _validate_count(value: int | None, name: str) -> None:
	if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
		raise ValueError(f"{name} must be a positive integer.")
