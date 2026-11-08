"""BookShelf Obsidian MCP server (MCP SDK 1.x)."""
from pathlib import Path
import os
import re
import subprocess

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("BookShelf-KB")
VAULT = Path(os.environ.get("BOOKSHELF_KB_PATH", r"C:\Users\user\BookShelf-KB"))
CATEGORIES = {"Components": "component", "Concepts": "concept", "Decisions": "decision", "Glossary": "glossary"}


def note_path(category: str, title: str) -> Path:
    if category not in CATEGORIES:
        raise ValueError("Unknown category")
    if title in (".", "..") or not re.fullmatch(r"[\w .()-]{1,100}", title, re.UNICODE):
        raise ValueError("Invalid title")
    return VAULT / category / (title + ".md")


def run_git(*args: str) -> str:
    # Never allow Git to wait for credentials or terminal prompts.
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    result = subprocess.run(
        ["git", "-C", str(VAULT), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        timeout=12,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


@mcp.tool()
def ping() -> str:
    """Check server availability."""
    return "BookShelf MCP server is working"


@mcp.tool()
def get_note(category: str, title: str) -> str:
    """Read a note from the Obsidian vault."""
    path = note_path(category, title)
    return path.read_text(encoding="utf-8") if path.is_file() else "NOT_FOUND"


@mcp.tool()
def ingest_note(category: str, title: str, content: str, links: list[str] | None = None) -> str:
    """Create/update a note locally, without network calls; idempotent."""
    path = note_path(category, title)
    if not VAULT.is_dir():
        return "ERROR: Vault not found"
    safe_links = []
    for link in links or []:
        if not re.fullmatch(r"[\w .()-]{1,100}", link, re.UNICODE) or link in (".", ".."):
            raise ValueError("Invalid link")
        safe_links.append(link)
    body = (
        "---\n"
        f"type: {CATEGORIES[category]}\n"
        "status: active\n"
        "project: BookShelf\n"
        "tags: [bookshelf, mcp]\n"
        "---\n"
        f"# {title}\n\n{content.strip()}\n"
    )
    if safe_links:
        body += "\n## Пов'язані нотатки\n" + "\n".join(f"[[{link}]]" for link in safe_links) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == body:
        return f"UNCHANGED: {category}/{title}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return f"SUCCESS: {category}/{title}.md (local; not pushed)"


@mcp.tool()
def sync_note(category: str, title: str) -> str:
    """Commit and push one existing note to GitHub. Call only after ingest_note."""
    path = note_path(category, title)
    if not path.is_file():
        return "NOT_FOUND"
    rel = path.relative_to(VAULT).as_posix()
    try:
        # No pull while local changes exist; never stage unrelated files.
        run_git("add", "--", rel)
        if not run_git("diff", "--cached", "--name-only", "--", rel):
            return f"UNCHANGED: {rel}"
        run_git("commit", "-m", f"docs: update {title}", "--", rel)
        run_git("push")
        return f"SYNCED: {rel}"
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        return f"SYNC_ERROR: {type(exc).__name__}: {exc}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
