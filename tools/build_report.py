#!/usr/bin/env python3
"""Machine-readable provenance, showing exactly which source and patch were built."""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    keys = ('MESA_REPO', 'MESA_REF', 'MESA_SHA', 'MESA_VERSION', 'PATCH_PROFILE',
            'PATCH_SHA', 'NDK_VERSION', 'NDK_REVISION', 'ANDROID_API',
            'VULKAN_BETA', 'VARIANT_NAME', 'BUILD_VERSION', 'ZIP_PATH', 'SHA256')
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'build and static checks only, no real-device Vulkan test',
              'parameters': {key.lower(): os.environ.get(key, '') for key in keys}}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'Report: {args.output}')


if __name__ == '__main__':
    main()
