#!/usr/bin/env python3
"""Summarize likely Vulkan/Turnip issues in ADB logcat dumps (heuristic only)."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

PATTERNS = {
    'device_lost': re.compile(r'VK_ERROR_DEVICE_LOST|device\s+lost', re.I),
    'driver_library': re.compile(r'libvulkan_freedreno|turnip|freedreno', re.I),
    'kgsl': re.compile(r'\bkgsl\b|ioctl_kgsl', re.I),
    'fatal': re.compile(r'fatal signal|SIGSEGV|SIGABRT|SIGBUS|backtrace:', re.I),
    'vulkan_failure': re.compile(r'VK_ERROR_[A-Z_]+|vulkan.*(fail|error)', re.I),
}


def analyze(text: str):
    lines = text.splitlines()
    counts = Counter()
    selected = []
    for line in lines:
        tags = [name for name, regex in PATTERNS.items() if regex.search(line)]
        for tag in tags:
            counts[tag] += 1
        if tags:
            selected.append({'tags': tags, 'line': line[:400]})
    return {'total_lines': len(lines), 'matches': dict(counts),
            'sample': selected[-40:],
            'warning': 'Log matches are indicators only, not proof of driver causality. Logs can contain private information.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('logfile', type=Path)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = analyze(args.logfile.read_text(encoding='utf-8', errors='replace'))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Analyzed {report['total_lines']} lines")
        for key, count in sorted(report['matches'].items()):
            print(f'{key}: {count}')
        print(report['warning'])


if __name__ == '__main__':
    main()
