"""Expose the legacy numeric test module to standard unittest discovery."""

from pathlib import Path
import runpy
import unittest


AddTests = runpy.run_path(str(Path(__file__).with_name("1.py")))["AddTests"]


if __name__ == "__main__":
    unittest.main()
