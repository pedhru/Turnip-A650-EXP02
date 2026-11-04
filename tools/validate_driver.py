#!/usr/bin/env python3
"""Static checks for libadrenotools Turnip ZIPs. Not a GPU runtime test."""
import argparse
import json
import re
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

DRIVER = 'libvulkan_freedreno.so'
REQUIRED = {'schemaVersion', 'name', 'description', 'author', 'packageVersion',
            'vendor', 'driverVersion', 'minApi', 'libraryName'}


class PackageError(ValueError):
    pass


def check_elf(data: bytes) -> None:
    if len(data) < 64 or data[:4] != b'\x7fELF':
        raise PackageError('Driver is not an ELF library')
    if data[4] != 2:
        raise PackageError('ELF must be 64-bit (arm64-v8a)')
    if data[5] != 1:
        raise PackageError('ELF must be little-endian')
    elf_type, machine = struct.unpack_from('<HH', data, 16)
    if elf_type != 3:
        raise PackageError(f'ELF must be shared ET_DYN, got {elf_type}')
    if machine != 183:
        raise PackageError(f'Expected EM_AARCH64 (183), got {machine}')


def check_meta(meta: dict) -> None:
    if not isinstance(meta, dict) or REQUIRED - meta.keys():
        raise PackageError(f'Missing meta.json attributes: {sorted(REQUIRED - meta.keys()) if isinstance(meta, dict) else "not an object"}')
    if type(meta['schemaVersion']) is not int or meta['schemaVersion'] != 1:
        raise PackageError('schemaVersion must be integer 1')
    if type(meta['minApi']) is not int or not 28 <= meta['minApi'] <= 36:
        raise PackageError('minApi must match supported Android target')
    if meta['libraryName'] != DRIVER:
        raise PackageError(f'libraryName must be {DRIVER}')
    if meta['vendor'] != 'Mesa':
        raise PackageError('Vendor must be Mesa')
    for key in ('name', 'description', 'author', 'packageVersion', 'driverVersion'):
        if not isinstance(meta[key], str) or not meta[key].strip():
            raise PackageError(f'Invalid metadata field: {key}')
    if len(meta['name']) > 128:
        raise PackageError('Driver display name too long')


def validate_zip(path: Path) -> tuple[dict, bytes]:
    if not path.is_file():
        raise PackageError(f'ZIP not found: {path}')
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise PackageError('ZIP integrity test failed')
        info = archive.infolist()
        names = [i.filename for i in info]
        if sorted(names) != sorted([DRIVER, 'meta.json']):
            raise PackageError(f'Unexpected ZIP contents: {names}')
        for entry in info:
            if entry.flag_bits & 1:
                raise PackageError('Encrypted ZIP entries are not supported')
            if entry.file_size > 256 * 1024 * 1024:
                raise PackageError('Unreasonable package entry size')
        meta = json.loads(archive.read('meta.json').decode('utf-8'))
        library = archive.read(DRIVER)
    check_meta(meta)
    check_elf(library)
    if len(library) < 100_000:
        raise PackageError('Turnip library suspiciously small')
    return meta, library


def inspect_dependencies(data: bytes, readelf: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp) / DRIVER
        library.write_bytes(data)
        result = subprocess.run([readelf, '-d', str(library)], capture_output=True, text=True)
    if result.returncode:
        raise PackageError(f'readelf failed: {result.stderr.strip()}')
    libs = re.findall(r'\(NEEDED\).*?\[([^\]]+)\]', result.stdout)
    if 'libdrm.so' in libs or any(dep.startswith('libdrm.so.') for dep in libs):
        raise PackageError('KGSL driver should not depend on libdrm.so on stock Android')
    return libs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('zip_file', type=Path)
    parser.add_argument('--readelf', default='readelf')
    args = parser.parse_args()
    try:
        meta, data = validate_zip(args.zip_file)
        deps = inspect_dependencies(data, args.readelf)
    except (PackageError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'INVALID DRIVER: {exc}', file=sys.stderr)
        return 1
    print(f"VALID: {args.zip_file.name}; {meta['driverVersion']}; min API {meta['minApi']}")
    print('ELF: 64-bit AArch64 shared object; dependencies: ' + (', '.join(deps) or 'none'))
    print('Note: GPU compatibility, Vulkan API version and FPS require on-device tests.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
