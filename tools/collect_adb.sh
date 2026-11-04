#!/usr/bin/env bash
# No root. Reads build properties and the most recent filtered diagnostic log lines.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
command -v adb >/dev/null || { echo 'Install adb/Android platform-tools first.' >&2; exit 1; }
count="$(adb devices | awk 'NR>1 && $2=="device" {n++} END {print n+0}')"
[[ "$count" == 1 ]] || { echo "Expected exactly one authorized ADB device; found $count" >&2; exit 1; }
out="${1:-$ROOT/device-diagnostics}"
mkdir -p "$out"
{
    printf 'Product: '; adb shell getprop ro.product.model
    printf 'Android API: '; adb shell getprop ro.build.version.sdk
    printf 'ABI: '; adb shell getprop ro.product.cpu.abi
    printf 'Chipset: '; adb shell getprop ro.board.platform
    printf 'Android version: '; adb shell getprop ro.build.version.release
} > "$out/device.txt"
# Match only likely relevant messages. Do not clear system logcat.
adb logcat -d -t 2500 2>/dev/null \
    | grep -Ei 'freedreno|turnip|vulkan|\bkgsl\b|fatal signal|SIGSEGV|SIGABRT|SIGBUS' \
    > "$out/filtered-logcat.txt" || true
python3 "$ROOT/tools/analyze_log.py" "$out/filtered-logcat.txt" > "$out/summary.txt"
printf 'Collected diagnostics under %s\n' "$out"
printf 'Review and redact logs before sharing; they may contain sensitive data.\n'
