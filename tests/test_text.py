from app.providers.speech.base import merge_turns
from app.utils.text import format_bytes, render_markdown, split_text


def test_markdown_renders_tables_and_headings():
    html = render_markdown("## Summary\n\n| Task | Owner |\n| --- | --- |\n| Ship | Ana |")
    assert "<h2>Summary</h2>" in html
    assert "<table>" in html and "<td>Ship</td>" in html


def test_markdown_strips_dangerous_output():
    html = render_markdown("Fine\n\n<script>alert(1)</script><img src=x onerror=alert(1)>")
    assert "<script>" not in html and "onerror" not in html


def test_split_text_keeps_short_input_whole():
    assert split_text("short", 100) == ["short"]


def test_split_text_respects_the_limit():
    text = "\n\n".join(f"paragraph {i} " * 20 for i in range(40))
    chunks = split_text(text, 1000)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
    assert sum(len(c.split()) for c in chunks) == len(text.split())


def test_split_text_breaks_up_one_huge_paragraph():
    chunks = split_text("x" * 5000, 1000)
    assert len(chunks) == 5 and all(len(c) == 1000 for c in chunks)


def test_merge_turns_labels_multiple_speakers():
    result = merge_turns([(0, "Hello"), (0, "everyone"), (1, "Hi"), (0, "Shall we start")])
    assert result == "[Speaker 0]: Hello everyone\n\n[Speaker 1]: Hi\n\n[Speaker 0]: Shall we start"


def test_merge_turns_drops_labels_for_a_single_speaker():
    assert merge_turns([(0, "Hello"), (0, "again")]) == "Hello again"


def test_merge_turns_ignores_empty_segments():
    assert merge_turns([(0, ""), (0, "   "), (None, "")]) == ""


def test_format_bytes():
    assert format_bytes(None) == "—"
    assert format_bytes(512) == "512 B"
    assert format_bytes(2 * 1024 * 1024) == "2.0 MB"
