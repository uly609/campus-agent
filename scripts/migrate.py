from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.database import create_all_tables


def main() -> None:
    create_all_tables()
    print("database metadata applied")


if __name__ == "__main__":
    main()

