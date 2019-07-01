from laforge.logo import get_version_display

COLOR_SYNTAX_PREFIX = "\033["


def test_version_display_includes_laforge_and_python_versions():
    clickable = get_version_display().lower()
    assert "laforge" in clickable
    assert "python" in clickable


def test_colored_display_includes_color_tags():
    clickable = get_version_display(monochrome=False).lower()
    assert COLOR_SYNTAX_PREFIX in clickable


def test_monochrome_display_excludes_color_tags():
    clickable = get_version_display(monochrome=True).lower()
    assert COLOR_SYNTAX_PREFIX not in clickable

