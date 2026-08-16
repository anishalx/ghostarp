"""Convenience entry point: ``python main.py`` (same as ``python -m ghostarp``)."""
from ghostarp.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
