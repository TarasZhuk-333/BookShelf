"""Build the local BookShelf KB index without writing to the Vault."""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp-server"))
from retrieval import DEFAULT_INDEX, DEFAULT_MODEL, RetrievalError, build_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=Path(os.environ.get("BOOKSHELF_KB_PATH", r"C:\Users\user\BookShelf-KB")))
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--allow-download", action="store_true", help="Allow initial model download; otherwise use cache only")
    args = parser.parse_args()
    try:
        count = build_index(args.vault, args.index_dir, args.model, allow_download=args.allow_download)
    except (RetrievalError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Indexed {count} chunks: {args.index_dir / 'index.npz'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
