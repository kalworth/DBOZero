"""Compatibility shim. The canonical, maintained module lives in
hanhua_v3.runtime.auto_translate_new_source; this shim keeps archived legacy scripts working.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hanhua_v3.runtime import auto_translate_new_source as _impl

sys.modules[__name__] = _impl
