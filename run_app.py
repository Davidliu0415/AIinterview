from __future__ import annotations

import multiprocessing
import threading
import webbrowser

import uvicorn

from app.config import get_settings
from app.main import app


def open_browser(url: str) -> None:
    webbrowser.open(url)


def main() -> None:
    multiprocessing.freeze_support()
    settings = get_settings()
    if settings.auto_open_browser:
        threading.Timer(1.2, open_browser, args=(settings.app_url,)).start()
    uvicorn.run(app, host=settings.app_host, port=settings.app_port, log_level="info")


if __name__ == "__main__":
    main()
