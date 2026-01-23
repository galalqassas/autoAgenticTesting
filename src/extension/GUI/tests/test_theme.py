"""Unit tests for theme module."""


from src.extension.GUI.theme import COLORS


class TestColors:
    """Tests for COLORS configuration."""

    def test_all_required_colors_exist(self):
        """All required colors should be defined."""
        required = [
            "bg_dark", "bg_card", "bg_header", "bg_console", "input_bg", "border",
            "text_primary", "text_secondary", "text_muted",
            "accent_green", "accent_blue", "accent_red",
            "button_primary", "button_hover", "button_stop",
        ]
        for key in required:
            assert key in COLORS, f"Missing color: {key}"

    def test_all_colors_valid_hex_format(self):
        """All colors should be valid #RRGGBB hex codes."""
        valid_hex = set("0123456789abcdefABCDEF")
        for key, value in COLORS.items():
            assert value.startswith("#") and len(value) == 7, f"{key}: invalid format"
            assert all(c in valid_hex for c in value[1:]), f"{key}: invalid hex digits"

    def test_colors_have_expected_values(self):
        """Spot-check key colors have expected values."""
        assert COLORS["bg_dark"] == "#1a1a1a"
        assert COLORS["accent_green"] == "#22c55e"
        assert COLORS["text_primary"] == "#ffffff"
