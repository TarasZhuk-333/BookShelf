"""Read-only Markdown retrieval; optional ML dependencies are loaded on demand."""
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_INDEX = Path(__file__).resolve().parents[1] / "artifacts" / "kb-index"
VERSION = 1


class RetrievalError(RuntimeError):
    """An unavailable, invalid or stale retrieval index."""


def snapshot(vault):
    """Read Markdown once, excluding hidden paths and links outside the vault."""
    vault = Path(vault).resolve()
    if not vault.is_dir():
        raise RetrievalError("Vault not found")
    notes = {}
    for root, dirs, files in os.walk(vault, followlinks=False):
        base = Path(root)
        dirs[:] = sorted(d for d in dirs if not d.startswith(".")
                         and not (base / d).is_symlink()
                         and not getattr(base / d, "is_junction", lambda: False)()
                         and (base / d).resolve().is_relative_to(vault))
        for name in sorted(files):
            path = base / name
            if name.startswith(".") or path.suffix.lower() != ".md" or path.is_symlink():
                continue
            if not path.resolve().is_relative_to(vault):
                continue
            notes[path.relative_to(vault).as_posix()] = path.read_bytes()
    return notes


def manifest(notes):
    return {path: hashlib.sha256(data).hexdigest() for path, data in sorted(notes.items())}


def chunk_markdown(text):
    """Split ATX/Setext headings, preserving fenced code and dropping YAML."""
    lines = text.lstrip("\ufeff").splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() in {"---", "..."}), None)
        if end is not None:
            lines = lines[end + 1:]
    chunks, current = [], []
    fence = None
    for line in lines:
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
            current.append(line)
            continue
        heading = fence is None and re.match(r"^ {0,3}#{1,6}(?:\s|$)", line)
        setext = fence is None and re.fullmatch(r" {0,3}(?:=+|-+)\s*", line) and current and current[-1].strip()
        if setext:
            title = current.pop()
            if "\n".join(current).strip():
                chunks.append("\n".join(current).strip())
            current = [title, line]
        elif heading:
            if "\n".join(current).strip():
                chunks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if "\n".join(current).strip():
        chunks.append("\n".join(current).strip())
    return chunks


def numpy():
    try:
        import numpy as np
    except ImportError as exc:
        raise RetrievalError("NumPy unavailable; install mcp-server/requirements.txt") from exc
    return np


def load_model(name, *, allow_download=False):
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(name, local_files_only=not allow_download)
    except (ImportError, OSError) as exc:
        raise RetrievalError("Embedding dependencies or cached model unavailable; build the index first") from exc


def normalize(values):
    np = numpy()
    values = np.asarray(values, dtype=np.float32)
    if values.ndim != 2 or not np.isfinite(values).all():
        raise RetrievalError("Invalid embedding matrix")
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    if (norms == 0).any():
        raise RetrievalError("Zero embedding")
    return values / norms


def build_index(vault, index_dir=DEFAULT_INDEX, model_name=DEFAULT_MODEL, *, encoder=None, allow_download=False):
    np = numpy()
    vault, index_dir = Path(vault).resolve(), Path(index_dir).resolve()
    if index_dir.is_relative_to(vault):
        raise RetrievalError("Index must be outside the read-only Vault")
    notes = snapshot(vault)
    chunks = [{"path": path, "fragment": chunk} for path, data in sorted(notes.items())
              for chunk in chunk_markdown(data.decode("utf-8-sig"))]
    if not chunks:
        raise RetrievalError("No Markdown chunks to index")
    encoder = encoder if encoder is not None else load_model(model_name, allow_download=allow_download)
    vectors = normalize(encoder.encode([c["fragment"] for c in chunks], show_progress_bar=False))
    if vectors.shape[0] != len(chunks):
        raise RetrievalError("Embedding count mismatch")
    metadata = dict(version=VERSION, vault=str(vault), model=model_name, manifest=manifest(notes), chunks=chunks)
    if manifest(snapshot(vault)) != metadata["manifest"]:
        raise RetrievalError("Vault changed during indexing; retry")
    index_dir.mkdir(parents=True, exist_ok=True)
    # One atomic artifact keeps vectors and metadata from different builds apart.
    handle, temporary = tempfile.mkstemp(dir=index_dir, suffix=".npz")
    os.close(handle)
    try:
        np.savez_compressed(temporary, vectors=vectors, metadata=json.dumps(metadata, ensure_ascii=False))
        os.replace(temporary, index_dir / "index.npz")
    finally:
        Path(temporary).unlink(missing_ok=True)
    return len(chunks)


def search(vault, query, top_k=5, index_dir=DEFAULT_INDEX, *, encoder=None):
    if not isinstance(query, str) or not query.strip():
        raise RetrievalError("query must not be empty")
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise RetrievalError("top_k must be a positive integer")
    np = numpy()
    try:
        with np.load(Path(index_dir) / "index.npz", allow_pickle=False) as data:
            metadata = json.loads(str(data["metadata"].item()))
            vectors = normalize(data["vectors"])
        if metadata["version"] != VERSION or metadata["vault"] != str(Path(vault).resolve()):
            raise RetrievalError("Index configuration mismatch; rebuild index")
        if metadata["manifest"] != manifest(snapshot(vault)):
            raise RetrievalError("Index stale: notes changed, added or deleted; rebuild index")
        chunks = metadata["chunks"]
        if len(chunks) != vectors.shape[0]:
            raise RetrievalError("Index chunk count mismatch; rebuild index")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RetrievalError("Index missing or invalid; rebuild index") from exc
    encoder = encoder if encoder is not None else load_model(metadata["model"])
    query_vector = normalize(encoder.encode([query.strip()], show_progress_bar=False))
    if query_vector.shape != (1, vectors.shape[1]):
        raise RetrievalError("Query embedding dimensions mismatch")
    scores = vectors @ query_vector[0]
    return [dict(chunks[int(i)], score=float(scores[i]))
            for i in np.argsort(-scores, kind="stable")[:top_k]]
