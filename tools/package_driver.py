#!/usr/bin/env python3
"""Create a minimal reproducible ADPKG ZIP with Turnip and strict metadata."""
import argparse
import json
import zipfile
from pathlib import Path

from validate_driver import DRIVER, check_elf, check_meta


def build_package(library: Path, output: Path, meta: dict) -> None:
    data = library.read_bytes()
    check_elf(data)
    if len(data) < 100_000:
        raise ValueError('Driver library suspiciously small')
    check_meta(meta)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(meta, indent=2, ensure_ascii=False, sort_keys=True).encode('utf-8') + b'\n'
    # Fixed timestamps & entry order, so the ZIP changes only when bytes change.
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, contents in ((DRIVER, data), ('meta.json', payload)):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, contents, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--description', required=True)
    p.add_argument('--author', required=True)
    p.add_argument('--driver-version', required=True)
    p.add_argument('--package-version', required=True)
    p.add_argument('--min-api', type=int, required=True)
    a = p.parse_args()
    meta = dict(schemaVersion=1, name=a.name, description=a.description,
                author=a.author, packageVersion=a.package_version,
                vendor='Mesa', driverVersion=a.driver_version,
                minApi=a.min_api, libraryName=DRIVER)
    build_package(a.library, a.output, meta)
    print(f'Packed: {a.output}')


if __name__ == '__main__':
    main()
