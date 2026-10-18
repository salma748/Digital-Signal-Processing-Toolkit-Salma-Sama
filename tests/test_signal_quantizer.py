import unittest

from core.signal_quantizer import quantize_signal
from models.signal import Signal


class QuantizeSignalTests(unittest.TestCase):
    def test_bits_calculate_levels_and_return_quantized_output(self):
        signal = Signal({8: -1.0, 3: 0.0, 10: 1.0})

        result = quantize_signal(signal, bits=3)

        self.assertEqual(result.interval_indices, [1, 5, 8])
        self.assertEqual(result.encoded_values, ["000", "100", "111"])
        self.assertEqual(
            result.quantized_signal.samples,
            {8: -0.875, 3: 0.125, 10: 0.875},
        )
        self.assertEqual(
            result.quantization_error.samples,
            {8: 0.125, 3: 0.125, 10: -0.125},
        )

    def test_levels_use_fixed_width_encoding_and_clamp_maximum(self):
        signal = Signal({5: -1.0, 2: -0.5, 9: 0.0, 1: 0.5, 7: 1.0})

        result = quantize_signal(signal, levels=4)

        self.assertEqual(result.interval_indices, [1, 2, 3, 4, 4])
        self.assertEqual(result.encoded_values, ["00", "01", "10", "11", "11"])
        self.assertEqual(
            result.quantized_signal.samples,
            {5: -0.75, 2: -0.25, 9: 0.25, 1: 0.75, 7: 0.75},
        )
        self.assertEqual(
            result.quantization_error.samples,
            {5: 0.25, 2: 0.25, 9: 0.25, 1: 0.25, 7: -0.25},
        )

    def test_constant_signal_reconstructs_exactly(self):
        signal = Signal({4: 2.5, 0: 2.5})

        result = quantize_signal(signal, levels=4)

        self.assertEqual(result.interval_indices, [1, 1])
        self.assertEqual(result.encoded_values, ["00", "00"])
        self.assertEqual(result.quantized_signal.samples, {4: 2.5, 0: 2.5})
        self.assertEqual(result.quantization_error.samples, {4: 0.0, 0: 0.0})

    def test_empty_signal_returns_empty_outputs(self):
        result = quantize_signal(Signal({}), bits=2)

        self.assertEqual(result.interval_indices, [])
        self.assertEqual(result.encoded_values, [])
        self.assertEqual(result.quantized_signal.samples, {})
        self.assertEqual(result.quantization_error.samples, {})

    def test_extreme_finite_range_is_supported(self):
        result = quantize_signal(Signal({0: -1e308, 1: 1e308}), levels=2)

        self.assertEqual(result.interval_indices, [1, 2])
        self.assertEqual(result.quantized_signal.samples, {0: -5e307, 1: 5e307})

    def test_rejects_missing_or_conflicting_count(self):
        signal = Signal({0: 1.0})

        with self.assertRaises(ValueError):
            quantize_signal(signal)
        with self.assertRaises(ValueError):
            quantize_signal(signal, bits=2, levels=4)

    def test_rejects_invalid_bit_and_level_counts(self):
        signal = Signal({0: 1.0})

        for invalid_bits in (0, -1, 1.5, True):
            with self.subTest(bits=invalid_bits):
                with self.assertRaises(ValueError):
                    quantize_signal(signal, bits=invalid_bits)

        for invalid_levels in (0, -2, 2.5, False):
            with self.subTest(levels=invalid_levels):
                with self.assertRaises(ValueError):
                    quantize_signal(signal, levels=invalid_levels)

    def test_rejects_non_finite_samples(self):
        for invalid_value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValueError):
                    quantize_signal(Signal({0: invalid_value}), levels=2)


if __name__ == "__main__":
    unittest.main()
