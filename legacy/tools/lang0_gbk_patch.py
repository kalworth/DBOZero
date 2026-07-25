"""Compatibility shim. The canonical, maintained module lives in
hanhua_v3.runtime.lang0_gbk_patch; this shim keeps archived legacy scripts working.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from hanhua_v3.runtime import lang0_gbk_patch as _impl

sys.modules[__name__] = _impl
