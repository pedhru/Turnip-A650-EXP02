import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from package_driver import build_package
from validate_driver import PackageError, check_elf, check_meta, validate_zip


class StaticPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.library = self.dir / 'libvulkan_freedreno.so'
        self.elf = bytearray(100_001)
        self.elf[:6] = b'\x7fELF\x02\x01'
        struct.pack_into('<HH', self.elf, 16, 3, 183)
        self.library.write_bytes(self.elf)
        self.meta = dict(schemaVersion=1, name='EXP12 test', description='Test only',
                         author='Test', packageVersion='1', vendor='Mesa',
                         driverVersion='Mesa test', minApi=33,
                         libraryName='libvulkan_freedreno.so')

    def test_valid_mock_package(self):
        out = self.dir / 'test.zip'
        build_package(self.library, out, self.meta)
        meta, lib = validate_zip(out)
        self.assertEqual(meta['name'], 'EXP12 test')
        self.assertEqual(len(lib), len(self.elf))

    def test_reproducible_zip_bytes(self):
        a, b = self.dir / 'a.zip', self.dir / 'b.zip'
        build_package(self.library, a, self.meta)
        build_package(self.library, b, self.meta)
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_reject_arm32(self):
        self.elf[4] = 1
        with self.assertRaises(PackageError):
            check_elf(self.elf)

    def test_reject_x86_64(self):
        struct.pack_into('<H', self.elf, 18, 62)
        with self.assertRaises(PackageError):
            check_elf(self.elf)

    def test_reject_elf_executable(self):
        struct.pack_into('<H', self.elf, 16, 2)
        with self.assertRaises(PackageError):
            check_elf(self.elf)

    def test_reject_wrong_library_name(self):
        bad = {**self.meta, 'libraryName': 'libvulkan_other.so'}
        with self.assertRaises(PackageError):
            check_meta(bad)

    def test_reject_missing_metadata(self):
        bad = dict(self.meta)
        bad.pop('minApi')
        with self.assertRaises(PackageError):
            check_meta(bad)

    def test_reject_unsupported_api(self):
        with self.assertRaises(PackageError):
            check_meta({**self.meta, 'minApi': 27})

    def test_reject_extra_file(self):
        out = self.dir / 'bad.zip'
        with zipfile.ZipFile(out, 'w') as z:
            z.writestr('meta.json', json.dumps(self.meta))
            z.writestr('libvulkan_freedreno.so', bytes(self.elf))
            z.writestr('other.txt', 'bad')
        with self.assertRaises(PackageError):
            validate_zip(out)

    def test_reject_tiny_library(self):
        self.library.write_bytes(self.elf[:128])
        with self.assertRaises(ValueError):
            build_package(self.library, self.dir / 'test.zip', self.meta)


if __name__ == '__main__':
    unittest.main()
