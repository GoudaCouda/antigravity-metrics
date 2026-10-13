#!/usr/bin/env python3
"""
Antigravity Conversation Token & Cost Inspector
===============================================
A lightweight, modern CLI plugin to inspect real-time token
consumption, cache savings, and accurate model costs for Google Antigravity.
"""

import sys
from pathlib import Path

# Ensure local package is importable when executed directly as a script
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from antigravity_metrics.cli import main

if __name__ == "__main__":
    main()
