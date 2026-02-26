"""Tests for Rich Console factory and theme."""

from io import StringIO

from ztlctl.output.console import (
    ZTL_THEME,
    create_console,
    get_output,
    style_for_type,
)


class TestCreateConsole:
    def test_returns_console_with_stringio(self) -> None:
        console = create_console()
        assert isinstance(console.file, StringIO)

    def test_no_color_disables_ansi(self) -> None:
        console = create_console(no_color=True)
        console.print("[bold red]hello[/bold red]")
        output = get_output(console)
        assert "\x1b" not in output
        assert "hello" in output

    def test_custom_width(self) -> None:
        console = create_console(width=80)
        assert console.width == 80

    def test_default_width(self) -> None:
        console = create_console()
        assert console.width == 120

    def test_highlight_disabled(self) -> None:
        console = create_console()
        # highlight=False prevents auto-highlighting of repr-like text
        # Print something that would normally get highlighted (e.g. a number)
        console.print("value=42")
        output = get_output(console)
        # No ANSI escape codes should be present
        assert "\x1b" not in output


class TestGetOutput:
    def test_extracts_printed_text(self) -> None:
        console = create_console(no_color=True)
        console.print("hello world")
        assert "hello world" in get_output(console)

    def test_empty_console(self) -> None:
        console = create_console()
        assert get_output(console) == ""


class TestStyleForType:
    def test_known_types(self) -> None:
        assert style_for_type("note") == "ztl.type.note"
        assert style_for_type("reference") == "ztl.type.reference"
        assert style_for_type("task") == "ztl.type.task"
        assert style_for_type("log") == "ztl.type.log"

    def test_unknown_type_returns_empty(self) -> None:
        assert style_for_type("unknown") == ""


class TestTheme:
    def test_theme_has_expected_styles(self) -> None:
        expected = [
            "ztl.ok",
            "ztl.error",
            "ztl.warning",
            "ztl.op",
            "ztl.key",
            "ztl.id",
            "ztl.path",
            "ztl.title",
            "ztl.type.note",
            "ztl.type.reference",
            "ztl.type.task",
            "ztl.type.log",
            "ztl.score",
        ]
        for name in expected:
            assert name in ZTL_THEME.styles, f"Missing theme style: {name}"
