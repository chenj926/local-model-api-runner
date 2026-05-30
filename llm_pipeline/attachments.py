from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path


TEXT_EXTENSIONS = {
    ".c",
    ".conf",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".env",
    ".go",
    ".h",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".log",
    ".md",
    ".php",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

LANGUAGE_BY_EXTENSION = {
    ".css": "css",
    ".csv": "csv",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsonl": "jsonl",
    ".jsx": "jsx",
    ".md": "markdown",
    ".php": "php",
    ".ps1": "powershell",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sql": "sql",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass(frozen=True)
class Attachment:
    path: Path
    relative_path: str
    content: str | None
    omitted_reason: str | None = None
    truncated: bool = False

    @property
    def included(self) -> bool:
        return self.content is not None


def collect_attachments(input_dir: Path, max_chars_per_file: int) -> list[Attachment]:
    if not input_dir.exists():
        return []

    attachments: list[Attachment] = []
    for path in sorted(item for item in input_dir.rglob("*") if item.is_file()):
        if _should_ignore_attachment(path):
            continue
        relative_path = path.relative_to(input_dir).as_posix()
        attachment = _read_attachment(path, relative_path, max_chars_per_file)
        attachments.append(attachment)
    return attachments


def render_attachments_for_prompt(attachments: list[Attachment]) -> str:
    included = [attachment for attachment in attachments if attachment.included]
    if not included:
        return ""

    blocks = ["Attached files from inputs/:"]
    for attachment in included:
        assert attachment.content is not None
        language = LANGUAGE_BY_EXTENSION.get(attachment.path.suffix.lower(), "")
        truncated_note = "\n[truncated]" if attachment.truncated else ""
        blocks.append(
            "\n".join(
                [
                    f"File: {attachment.relative_path}{truncated_note}",
                    f"````{language}",
                    attachment.content,
                    "````",
                ]
            )
        )
    return "\n\n".join(blocks)


def skipped_attachment_summary(attachments: list[Attachment]) -> list[str]:
    skipped = []
    for attachment in attachments:
        if attachment.omitted_reason:
            skipped.append(f"{attachment.relative_path}: {attachment.omitted_reason}")
    return skipped


def _read_attachment(path: Path, relative_path: str, max_chars: int) -> Attachment:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _read_pdf(path, relative_path, max_chars)

    if _looks_text_like(path):
        return _read_text(path, relative_path, max_chars)

    return Attachment(
        path=path,
        relative_path=relative_path,
        content=None,
        omitted_reason="binary or unsupported file type",
    )


def _should_ignore_attachment(path: Path) -> bool:
    return path.name in {".gitkeep", ".DS_Store", "Thumbs.db"}


def _looks_text_like(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return True

    mime_type, _ = mimetypes.guess_type(str(path))
    return bool(mime_type and mime_type.startswith("text/"))


def _read_text(path: Path, relative_path: str, max_chars: int) -> Attachment:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            content = path.read_text(encoding=encoding)
            return _truncate(path, relative_path, content, max_chars)
        except UnicodeDecodeError:
            continue

    return Attachment(
        path=path,
        relative_path=relative_path,
        content=None,
        omitted_reason="could not decode as text",
    )


def _read_pdf(path: Path, relative_path: str, max_chars: int) -> Attachment:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except ImportError:
        return Attachment(
            path=path,
            relative_path=relative_path,
            content=None,
            omitted_reason="PDF support requires: pip install pypdf",
        )

    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001 - keep attachment failures non-fatal.
        return Attachment(
            path=path,
            relative_path=relative_path,
            content=None,
            omitted_reason=f"could not read PDF: {exc}",
        )

    content = "\n\n".join(pages).strip()
    if not content:
        return Attachment(
            path=path,
            relative_path=relative_path,
            content=None,
            omitted_reason="PDF contained no extractable text",
        )
    return _truncate(path, relative_path, content, max_chars)


def _truncate(path: Path, relative_path: str, content: str, max_chars: int) -> Attachment:
    if len(content) <= max_chars:
        return Attachment(path=path, relative_path=relative_path, content=content)

    truncated_content = content[:max_chars].rstrip()
    return Attachment(
        path=path,
        relative_path=relative_path,
        content=truncated_content,
        truncated=True,
    )
