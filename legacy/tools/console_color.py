"""Compatibility shim. The canonical, maintained module lives in
hanhua_v3.runtime.console_color; this shim keeps archived legacy scripts working.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hanhua_v3.runtime import console_color as _impl

sys.modules[__name__] = _impl
