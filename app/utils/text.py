import markdown as markdown_lib
import nh3


def render_markdown(value: str | None) -> str:
    """Markdown to HTML, sanitised. Model output is never trusted."""
    if not value:
        return ""
    html = markdown_lib.markdown(value, extensions=["tables", "sane_lists", "nl2br"])
    return nh3.clean(html)


def split_text(text: str, chunk_chars: int) -> list[str]:
    """Split on paragraph boundaries into chunks no larger than chunk_chars."""
    if chunk_chars <= 0 or len(text) <= chunk_chars:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        block = paragraph if len(paragraph) <= chunk_chars else None
        if block is None:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(
                paragraph[i:i + chunk_chars] for i in range(0, len(paragraph), chunk_chars)
            )
            continue
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) > chunk_chars:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def format_bytes(size: int | float | None) -> str:
    if not size:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
