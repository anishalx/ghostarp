"""Enable running GhostARP with ``python -m ghostarp``."""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
