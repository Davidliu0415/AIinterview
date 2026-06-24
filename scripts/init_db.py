from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.database import init_db


def main() -> None:
    settings = get_settings()
    init_db()
    print(f"MySQL database ready: {settings.mysql_database}")


if __name__ == "__main__":
    main()
