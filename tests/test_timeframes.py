"""Unit tests for timeframe validation and conversion."""

import pytest

# MetaTrader5 ships Windows-only wheels; skip this module (which imports it, and
# through it the local backend) when it isn't installed, e.g. on Linux/macOS.
# CI runs the unit suite on Windows, where it is present.
mt5 = pytest.importorskip("MetaTrader5")

from mcp_mt5.main import get_timeframe_constant, timeframe_map  # noqa: E402


@pytest.mark.unit
class TestTimeframeValidation:
    """Test timeframe validation and conversion."""

    def test_all_timeframes_in_map(self):
        """Test that all expected timeframes are in the map."""
        expected_timeframes = [
            1,
            2,
            3,
            4,
            5,
            6,
            10,
            12,
            15,
            20,
            30,  # Minutes
            60,
            120,
            180,
            240,
            360,
            480,
            720,  # Hours
            1440,
            10080,
            43200,  # Days/Weeks/Months
        ]

        for tf in expected_timeframes:
            assert tf in timeframe_map, f"Timeframe {tf} not in map"

    def test_timeframe_count(self):
        """Test that we have all 21 standard MT5 timeframes."""
        assert len(timeframe_map) == 21, "Should have 21 timeframes"

    def test_valid_timeframe_conversion(self):
        """Test conversion of valid timeframes."""
        # Test minutes
        assert get_timeframe_constant(1) == mt5.TIMEFRAME_M1
        assert get_timeframe_constant(5) == mt5.TIMEFRAME_M5
        assert get_timeframe_constant(15) == mt5.TIMEFRAME_M15
        assert get_timeframe_constant(30) == mt5.TIMEFRAME_M30

        # Test hours
        assert get_timeframe_constant(60) == mt5.TIMEFRAME_H1
        assert get_timeframe_constant(240) == mt5.TIMEFRAME_H4

        # Test days/weeks/months
        assert get_timeframe_constant(1440) == mt5.TIMEFRAME_D1
        assert get_timeframe_constant(10080) == mt5.TIMEFRAME_W1
        assert get_timeframe_constant(43200) == mt5.TIMEFRAME_MN1

    def test_invalid_timeframe_raises_error(self):
        """Test that invalid timeframes raise ValueError."""
        invalid_timeframes = [0, 7, 25, 99, 999, 5000]

        for tf in invalid_timeframes:
            with pytest.raises(ValueError, match="Unsupported timeframe"):
                get_timeframe_constant(tf)

    def test_error_message_contains_supported_list(self):
        """Test that error message lists all supported timeframes."""
        try:
            get_timeframe_constant(999)
        except ValueError as e:
            error_msg = str(e)
            assert "Unsupported timeframe: 999" in error_msg
            assert "Supported timeframes" in error_msg
            # Check that some known timeframes are in the message
            assert "1" in error_msg
            assert "60" in error_msg
            assert "1440" in error_msg

    def test_all_new_timeframes_added(self):
        """Test that newly added timeframes are present."""
        new_timeframes = [2, 3, 4, 6, 10, 12, 20, 120, 180, 360, 480, 720]

        for tf in new_timeframes:
            assert tf in timeframe_map, f"New timeframe {tf} not in map"
            # Should not raise error
            result = get_timeframe_constant(tf)
            assert result is not None

    def test_timeframe_map_values_are_mt5_constants(self):
        """Test that all map values are valid MT5 constants."""
        # All values should be integers (MT5 constants)
        for tf_value in timeframe_map.values():
            assert isinstance(tf_value, int), f"Timeframe value {tf_value} is not an integer"

    @pytest.mark.parametrize(
        "minutes,expected_constant",
        [
            (1, mt5.TIMEFRAME_M1),
            (2, mt5.TIMEFRAME_M2),
            (3, mt5.TIMEFRAME_M3),
            (4, mt5.TIMEFRAME_M4),
            (5, mt5.TIMEFRAME_M5),
            (6, mt5.TIMEFRAME_M6),
            (10, mt5.TIMEFRAME_M10),
            (12, mt5.TIMEFRAME_M12),
            (15, mt5.TIMEFRAME_M15),
            (20, mt5.TIMEFRAME_M20),
            (30, mt5.TIMEFRAME_M30),
            (60, mt5.TIMEFRAME_H1),
            (120, mt5.TIMEFRAME_H2),
            (180, mt5.TIMEFRAME_H3),
            (240, mt5.TIMEFRAME_H4),
            (360, mt5.TIMEFRAME_H6),
            (480, mt5.TIMEFRAME_H8),
            (720, mt5.TIMEFRAME_H12),
            (1440, mt5.TIMEFRAME_D1),
            (10080, mt5.TIMEFRAME_W1),
            (43200, mt5.TIMEFRAME_MN1),
        ],
    )
    def test_each_timeframe_individually(self, minutes, expected_constant):
        """Test each timeframe conversion individually."""
        result = get_timeframe_constant(minutes)
        assert result == expected_constant
