from laforge.logo import get_version_display

COLOR_SYNTAX_PREFIX = "\033["


class TestVersionDisplay:
    def test_includes_laforge_and_python_versions(self):
        clickable = get_version_display().lower()
        assert "laforge" in clickable
        assert "python" in clickable

    def test_colored_includes_color_tags(self):
        clickable = get_version_display(monochrome=False).lower()
        assert COLOR_SYNTAX_PREFIX in clickable

    def test_monochrome_excludes_color_tags(self):
        clickable = get_version_display(monochrome=True).lower()
        assert COLOR_SYNTAX_PREFIX not in clickable
