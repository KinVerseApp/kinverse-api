from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI


logger = logging.getLogger("kinverse.api")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)


def configure_telemetry(app: FastAPI) -> None:
    app.state.logger = logger
    app.state.telemetry_enabled = True


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "kinverse.api")
