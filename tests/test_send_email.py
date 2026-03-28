"""Tests for src/send_email.py — convert_section and append_section."""

from send_email import convert_section, append_section


# ── convert_section ────────────────────────────────────────────────────────────

class TestConvertSection:
    def test_bold_markdown_becomes_html(self):
        result = convert_section("**bold text**")
        assert "<strong>bold text</strong>" in result

    def test_heading_becomes_h1(self):
        result = convert_section("# Hello")
        assert "<h1>" in result
        assert "Hello" in result

    def test_paragraph_text(self):
        result = convert_section("Just some text.")
        assert "Just some text." in result

    def test_empty_string_returns_none(self):
        assert convert_section("") is None

    def test_none_returns_none(self):
        assert convert_section(None) is None

    def test_code_block_gets_pre_style(self):
        result = convert_section("```\ncode here\n```")
        assert 'white-space: pre' in result


# ── append_section ─────────────────────────────────────────────────────────────

class TestAppendSection:
    def test_adds_content_to_text_and_html(self):
        text, html = append_section("", "", "# Weather\nSunny today.", "weather")
        assert "Weather" in text
        assert "<div class='section weather'>" in html

    def test_empty_content_leaves_existing_unchanged(self):
        text, html = append_section("existing text", "<p>existing</p>", "", "weather")
        assert text == "existing text"
        assert html == "<p>existing</p>"

    def test_whitespace_only_content_leaves_existing_unchanged(self):
        text, html = append_section("existing", "<p>hi</p>", "   ", "weather")
        assert text == "existing"
        assert html == "<p>hi</p>"

    def test_is_date_true_skips_html(self):
        # When is_date=True, the HTML div should NOT be appended
        _, html = append_section("", "", "Monday, January 15", "date", is_date=True)
        assert html == ""

    def test_text_format_false_skips_plain_text(self):
        text, _ = append_section("existing", "", "# Content", "section", text_format=False)
        assert text == "existing"
