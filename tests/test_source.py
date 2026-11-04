#!/usr/bin/env python3
"""Conservative release gate: no unverified Mesa27-specific source modifications."""
import sys
from pathlib import Path
src=Path(sys.argv[1]); version=(src/'VERSION').read_text().strip()
assert version=='26.2.6', f'Expected official Mesa 26.2.6, got {version}'
for path in ('src/freedreno/vulkan/tu_knl_kgsl.cc', 'src/freedreno/vulkan/tu_shader.cc', 'src/freedreno/vulkan/tu_device.cc'):
    assert (src/path).is_file(),f'Missing upstream file: {path}'
print('PASS: original official Mesa 26.2.6 tree and Turnip files found')
