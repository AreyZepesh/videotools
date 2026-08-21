import json # config.py, mediainfo.py

from pathlib import Path # config.py, ffmpeg.py, mediainfo.py, runners.py, gui.py
from dataclasses import dataclass # config.py, mediainfo.py
from typing import Literal # config.py, runners.py


def str_to_int(value, default=None):
    if isinstance(value, (int, float)):
        return int(value)

    digits = "".join(c for c in str(value or "") if c.isdecimal())
    return int(digits) if digits else default

def str_to_float(value, default=None):
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value or "").strip().replace(",", ".")

    allowed = "0123456789.-"
    filtered = "".join(c for c in s if c in allowed)

    return float(filtered) if filtered else default


if __name__ == "__main__":
    pass