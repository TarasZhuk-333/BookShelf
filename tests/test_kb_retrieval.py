"""Deterministic retrieval tests; never download a model or use the real Vault."""
import ast
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kb_retrieval", ROOT / "mcp-server" / "retrieval.py")
retrieval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retrieval)


class Encoder:
    def encode(self, texts, **kwargs):
        return [[1.0, 0.0] if "SQLite" in text else [0.0, 1.0] for text in texts]


def test_markdown_headings_frontmatter_and_fenced_code():
    text = "---\ntags: [test]\n---\n# One\nText\n```md\n# Code\n```\n## Two\nOther"
    assert retrieval.chunk_markdown(text) == ["# One\nText\n```md\n# Code\n```", "## Two\nOther"]
    assert retrieval.chunk_markdown("Intro\n\nTitle\n=====\nBody") == ["Intro", "Title\n=====\nBody"]
    assert retrieval.chunk_markdown("\n ") == []


def test_snapshot_excludes_hidden_paths(tmp_path):
    (tmp_path / "Note.md").write_text("Hello", encoding="utf-8")
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "hidden.md").write_text("Hidden", encoding="utf-8")
    (tmp_path / ".secret.md").write_text("Hidden", encoding="utf-8")
    assert list(retrieval.snapshot(tmp_path)) == ["Note.md"]


@pytest.fixture
def indexed(tmp_path):
    pytest.importorskip("numpy")
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Storage.md").write_text("# Storage\nSQLite database", encoding="utf-8")
    (vault / "UI.md").write_text("# Interface\nStreamlit", encoding="utf-8")
    before = retrieval.snapshot(vault)
    index = tmp_path / "index"
    assert retrieval.build_index(vault, index, encoder=Encoder()) == 2
    assert retrieval.snapshot(vault) == before
    return vault, index


def test_cosine_ranking_and_result_contract(indexed):
    vault, index = indexed
    results = retrieval.search(vault, "SQLite", 1, index, encoder=Encoder())
    assert results == [{"path": "Storage.md", "fragment": "# Storage\nSQLite database", "score": 1.0}]
    assert len(retrieval.search(vault, "SQLite", 99, index, encoder=Encoder())) == 2


@pytest.mark.parametrize("mutation", ["edit", "add", "delete"])
def test_stale_index_requires_rebuild_before_model_load(indexed, mutation, monkeypatch):
    vault, index = indexed
    if mutation == "edit":
        # Same byte length: content hashing must catch this too.
        path = vault / "UI.md"
        path.write_bytes(path.read_bytes().replace(b"Streamlit", b"Something"))
    elif mutation == "add":
        (vault / "New.md").write_text("New note", encoding="utf-8")
    else:
        (vault / "UI.md").unlink()
    monkeypatch.setattr(retrieval, "load_model", lambda *a, **k: pytest.fail("Model must not load for stale index"))
    with pytest.raises(retrieval.RetrievalError, match="stale"):
        retrieval.search(vault, "SQLite", index_dir=index)
    retrieval.build_index(vault, index, encoder=Encoder())
    assert retrieval.search(vault, "SQLite", index_dir=index, encoder=Encoder())


def test_missing_and_corrupt_index(tmp_path):
    pytest.importorskip("numpy")
    with pytest.raises(retrieval.RetrievalError, match="missing or invalid"):
        retrieval.search(tmp_path, "test", index_dir=tmp_path)
    (tmp_path / "index.npz").write_bytes(b"invalid")
    with pytest.raises(retrieval.RetrievalError, match="missing or invalid"):
        retrieval.search(tmp_path, "test", index_dir=tmp_path)


@pytest.mark.parametrize("query, top_k", [(" ", 5), ("test", 0), ("test", True), ("test", 1.5)])
def test_input_validation(query, top_k, tmp_path):
    with pytest.raises(retrieval.RetrievalError):
        retrieval.search(tmp_path, query, top_k)


def test_index_inside_vault_is_rejected(tmp_path):
    pytest.importorskip("numpy")
    with pytest.raises(retrieval.RetrievalError, match="outside"):
        retrieval.build_index(tmp_path, tmp_path / "index", encoder=Encoder())


def test_missing_dependencies_have_explicit_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(retrieval.RetrievalError, match="unavailable"):
        retrieval.load_model("unused")


def test_mcp_wrapper_and_lazy_dependency_loading(monkeypatch):
    pytest.importorskip("mcp")
    monkeypatch.setitem(sys.modules, "retrieval", retrieval)
    server_spec = importlib.util.spec_from_file_location("kb_test_server", ROOT / "mcp-server" / "server.py")
    server = importlib.util.module_from_spec(server_spec)
    server_spec.loader.exec_module(server)
    assert server.ping() == "BookShelf MCP server is working"
    def unavailable(*args):
        raise retrieval.RetrievalError("Index stale; rebuild index")
    monkeypatch.setattr(retrieval, "search", unavailable)
    assert server.search_notes("test") == {"results": [], "error": "Index stale; rebuild index"}


def test_retrieval_has_no_eager_ml_imports():
    tree = ast.parse((ROOT / "mcp-server" / "retrieval.py").read_text(encoding="utf-8"))
    imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all("numpy" not in ast.unparse(node) and "sentence_transformers" not in ast.unparse(node) for node in imports)
