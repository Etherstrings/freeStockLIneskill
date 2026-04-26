#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys
import warnings


warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL.*")


RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
if RUNTIME_DIR.is_dir():
    runtime_path = str(RUNTIME_DIR)
    if runtime_path not in sys.path:
        sys.path.insert(0, runtime_path)

from freestocklineskill_runtime.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
