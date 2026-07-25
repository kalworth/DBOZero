# -*- coding: utf-8 -*-
"""Small ANSI color helpers for terminal output."""

from __future__ import annotations

import os
import sys


GREEN = "32"
RED = "31"
CYAN = "36"


def supports_color(stream=None) -> bool:
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(stream, "isatty") and stream.isatty()


def color(text: str, code: str, stream=None) -> str:
    if not supports_color(stream):
        return text
    return f"\033[{code}m{text}\033[0m"


def ok(text: str, stream=None) -> str:
    return color(text, GREEN, stream)


def error(text: str, stream=None) -> str:
    return color(text, RED, stream)


def path(text: str, stream=None) -> str:
    return color(text, CYAN, stream)
