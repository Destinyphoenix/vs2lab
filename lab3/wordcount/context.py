"""Erweitert den Modul-Suchpfad um das Repo-Root, damit lib.lab_logging importierbar ist (wie in lab2)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from lib import lab_logging  # noqa: E402
