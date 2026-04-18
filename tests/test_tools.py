"""Unit tests for all tools."""

from __future__ import annotations

from src.tools.base import Tool, ToolRegistry
from src.tools.calculator import Calculator, safe_calculate
from src.tools.file_reader import FileReader
from src.tools.web_fetch import html_to_text


class TestCalculator:
    def test_basic_addition(self):
        assert safe_calculate("2 + 3") == 5

    def test_multiplication(self):
        assert safe_calculate("6 * 7") == 42

    def test_power(self):
        assert safe_calculate("2 ** 10") == 1024

    def test_sqrt(self):
        assert safe_calculate("sqrt(144)") == 12.0

    def test_combined(self):
        assert safe_calculate("sqrt(144) + 3**4") == 93.0

    def test_pi(self):
        result = safe_calculate("pi")
        assert abs(result - 3.14159) < 0.001

    def test_division_by_zero(self):
        calc = Calculator()
        result = calc.execute(expression="1/0")
        assert "Error" in result

    def test_invalid_expression(self):
        calc = Calculator()
        result = calc.execute(expression="import os")
        assert "Error" in result

    def test_protocol_compliance(self):
        calc = Calculator()
        assert isinstance(calc, Tool)
        assert calc.name == "calculator"
        assert "expression" in calc.input_schema["properties"]


class TestFileReader:
    def test_read_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        reader = FileReader([str(tmp_path)])
        result = reader.execute(path=str(f))
        assert result == "hello world"

    def test_path_denied(self, tmp_path):
        reader = FileReader([str(tmp_path / "allowed")])
        result = reader.execute(path="/etc/passwd")
        assert "denied" in result.lower() or "Error" in result

    def test_file_not_found(self, tmp_path):
        reader = FileReader([str(tmp_path)])
        result = reader.execute(path=str(tmp_path / "nope.txt"))
        assert "not found" in result.lower() or "Error" in result

    def test_no_path(self):
        reader = FileReader()
        result = reader.execute()
        assert "Error" in result

    def test_protocol_compliance(self):
        reader = FileReader()
        assert isinstance(reader, Tool)
        assert reader.name == "file_reader"


class TestHtmlToText:
    def test_strip_tags(self):
        assert html_to_text("<p>Hello</p>") == "Hello"

    def test_strip_script(self):
        html = "<script>alert('x')</script><p>Safe</p>"
        result = html_to_text(html)
        assert "alert" not in result
        assert "Safe" in result

    def test_truncation(self):
        html = "<p>" + "a" * 6000 + "</p>"
        result = html_to_text(html, max_length=100)
        assert len(result) < 200
        assert "truncated" in result

    def test_entities(self):
        result = html_to_text("&amp; &lt; &gt;")
        assert "& < >" in result


class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        calc = Calculator()
        reg.register(calc)
        assert reg.get("calculator") is calc

    def test_list_tools(self):
        reg = ToolRegistry()
        reg.register(Calculator())
        reg.register(FileReader())
        names = reg.list_tools()
        assert names == ["calculator", "file_reader"]

    def test_to_claude_tools(self):
        reg = ToolRegistry()
        reg.register(Calculator())
        tools = reg.to_claude_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "calculator"
        assert "input_schema" in tools[0]

    def test_unknown_tool(self):
        reg = ToolRegistry()
        assert reg.get("nonexistent") is None
