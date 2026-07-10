# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

# Module registry — subpackages are loaded on demand by server.py via importlib.
# Do not import them here to avoid triggering optional dependencies (e.g. BART)
# when a different module is selected.

__all__ = [
    "r2ci_bart",
    "i2i_invertcontrast",
]
