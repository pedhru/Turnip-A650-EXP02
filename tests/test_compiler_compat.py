"""Compiler compatibility regression tests for GitHub run 41748637122.

Fixtures are intentionally tiny; these tests do NOT compile the full Mesa.
"""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from fix_mesa_narrowing import RULES, prepare_patch


class CompilerCompatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.mesa = Path(self.tmp.name) / 'mesa'
        self.mesa.mkdir()
        self.original = {}
        for rel, rules in RULES.items():
            p = self.mesa / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            content = '// EXP13 log reproduction\n' + '\n'.join(x for x, _ in rules) + '\n'
            p.write_text(content)
            self.original[rel] = content

    def run_fix(self, *flags, check=True):
        return subprocess.run([sys.executable, str(ROOT/'tools/fix_mesa_narrowing.py'),
                               '--mesa-dir', str(self.mesa), *flags],
                              text=True, capture_output=True, check=check)

    def test_fixes_exactly_four_sites_and_records_sha(self):
        report = Path(self.tmp.name) / 'report.json'
        result = self.run_fix('--report', str(report))
        data = json.loads(result.stdout)
        self.assertEqual(data['fixed_sites'], 4)
        self.assertTrue(report.is_file())
        self.assertTrue(all(x['sha256_original'] != x['sha256_patched'] for x in data['files']))
        for rel, rules in RULES.items():
            text = (self.mesa/rel).read_text()
            for original, fixed in rules:
                self.assertIn(fixed, text)
                self.assertFalse(re.search((r'(?<!\(uint32_t\))' if 'gmem_align_h)};' in original else '') + re.escape(original), text))

    def test_idempotence(self):
        self.run_fix()
        before = {rel: (self.mesa/rel).read_bytes() for rel in RULES}
        second = json.loads(self.run_fix().stdout)
        self.assertEqual(second['fixed_sites'], 0)
        self.assertEqual(before, {rel: (self.mesa/rel).read_bytes() for rel in RULES})

    def test_check_only_leaves_files_unchanged(self):
        data = json.loads(self.run_fix('--check').stdout)
        self.assertEqual(data['fixed_sites'], 4)
        self.assertEqual(self.original, {rel: (self.mesa/rel).read_text() for rel in RULES})

    def test_fail_closed_on_ambiguous_duplicate(self):
        rel = next(iter(RULES))
        p = self.mesa/rel
        p.write_text(p.read_text() + RULES[rel][0][0] + '\n')
        before = {r: (self.mesa/r).read_bytes() for r in RULES}
        with self.assertRaises(ValueError):
            prepare_patch(self.mesa)
        self.assertEqual(before, {r: (self.mesa/r).read_bytes() for r in RULES})

    def test_fail_closed_missing_mesa_header(self):
        (self.mesa/'src/freedreno/fdl/freedreno_lrz_layout.h').unlink()
        result = self.run_fix(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Mesa source file missing', result.stderr)

    def test_static_c_and_cpp_compilers(self):
        """Ensure the explicit conversion is legal in both C11 and C++17."""
        source = r'''
#include <stdint.h>
#include <stddef.h>
struct Entry { size_t size; };
struct Meta { uint16_t size; };
struct U32 { uint32_t w; uint32_t h; };
struct Info { uint32_t gmem_align_w; uint32_t gmem_align_h; };
static inline size_t util_round_down_npot(size_t n, uint32_t a) { return n - n % a; }
static struct Meta first(struct Entry entry) { return (struct Meta){.size = (uint16_t)(entry.size / sizeof(uint32_t))}; }
static struct Meta second(uint32_t size) { return (struct Meta){.size = (uint16_t)size}; }
static struct U32 third(size_t max_extra_size, const struct Info *dev_info) {
  return (struct U32){(uint32_t)util_round_down_npot(max_extra_size, dev_info->gmem_align_w),
    (uint32_t)util_round_down_npot(max_extra_size, dev_info->gmem_align_h)};
}
'''
        # In C++, C-style designated struct literal is allowed by gnu++17 extensions;
        # use only syntax check to verify the casts in both languages.
        p = Path(self.tmp.name)/'probe.cpp'
        p.write_text(source)
        for lang, ext in [('c', 'c'), ('c++', 'cpp')]:
            probe = p.with_suffix('.'+ext)
            probe.write_text(source)
            compiler = 'cc' if lang == 'c' else 'c++'
            r = subprocess.run([compiler,'-fsyntax-only','-std=c11' if lang == 'c' else '-std=gnu++17',str(probe)],
                               text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)

if __name__ == '__main__':
    unittest.main()
