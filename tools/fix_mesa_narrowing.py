#!/usr/bin/env python3
"""Targeted Mesa C/C++ narrowing compatibility for the logged 2026-11-04 Turnip failure.

Explicit C-style casts retain the implicit conversion behavior already used by C,
while satisfying Clang C++17's list-initialization rule. This is a build fix, NOT a
runtime correctness or performance improvement; size-overflow is not addressed.

Fails closed for missing source files or ambiguous multiple occurrences. All
source modifications and their SHA256 hashes are recorded for provenance.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

# Exact source expressions taken from the failed GitHub build at Mesa
# 98a55f454dff645be1c88284634126a2c17fd416.
RULES = {
    "src/freedreno/vulkan/tu_cs.h": (
        (".size = entry.size / sizeof(uint32_t),", ".size = (uint16_t)(entry.size / sizeof(uint32_t)),"),
        (".size = size,", ".size = (uint16_t)size,"),
    ),
    "src/freedreno/fdl/freedreno_lrz_layout.h": (
        ("return {util_round_down_npot(max_extra_size, dev_info->gmem_align_w),", "return {(uint32_t)util_round_down_npot(max_extra_size, dev_info->gmem_align_w),"),
        ("util_round_down_npot(max_extra_size, dev_info->gmem_align_h)};", "(uint32_t)util_round_down_npot(max_extra_size, dev_info->gmem_align_h)};"),
    ),
}


def sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def prepare_patch(mesa_dir: Path):
    """Compute all edits without touching files, so errors cannot partially patch."""
    patches = []
    diagnostics = []
    for relative, rules in RULES.items():
        file = mesa_dir / relative
        if not file.is_file():
            raise ValueError(f'Mesa source file missing: {relative}')
        old = file.read_bytes()
        source = old.decode('utf-8')
        content = source
        counts = []
        for original, replacement in rules:
            # The 2nd layout expression is a suffix of the fixed form; use
            # a negative lookbehind so re-running the fix is idempotent.
            prefix = r'(?<!\(uint32_t\))' if 'gmem_align_h)};' in original else ''
            pattern = prefix + re.escape(original)
            occurrences = len(re.findall(pattern, content))
            if occurrences > 1:
                raise ValueError(f'Ambiguous Mesa source: {relative}: {original!r} occurs {occurrences} times')
            if occurrences and replacement in content:
                raise ValueError(f'Ambiguous partial upstream change: {relative}: {original!r}')
            content = re.sub(pattern, lambda _: replacement, content)
            counts.append(occurrences)
        patches.append((file, old, content.encode('utf-8')))
        diagnostics.append({'file': relative, 'fixes_applied': sum(counts),
                            'rule_matches': counts, 'sha256_original': sha256(old),
                            'sha256_patched': sha256(content.encode('utf-8'))})
    return patches, diagnostics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mesa-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--check', action='store_true', help='verify patches without changing files')
    args = parser.parse_args()
    patches, diagnostics = prepare_patch(args.mesa_dir)
    if not args.check:
        for filename, previous, updated in patches:
            if updated != previous:
                filename.write_bytes(updated)
    summary = {'status': 'dry-run' if args.check else 'applied',
               'scope': 'compiler-only explicit integer conversions; no GPU validation',
               'fixed_sites': sum(x['fixes_applied'] for x in diagnostics),
               'files': diagnostics}
    if args.report and not args.check:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(summary, indent=2, sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__ == '__main__':
    main()
