#!/usr/bin/env bash
set -Eeuo pipefail
trap 'echo "ERROR: EXP19 build failed at line ${LINENO}" >&2' ERR
recipe_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
[[ "$(uname -s)/$(uname -m)" == Linux/x86_64 ]] || { echo 'Linux x86_64 required' >&2; exit 1; }
work_dir="${WORK_DIR:-$recipe_dir/work-exp19}"
mkdir -p "$work_dir"
for tool in python3 meson ninja curl sha256sum tar unzip patch pkg-config bison flex m4 glslangValidator; do
 command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
python3 -c 'import mako,yaml,packaging,ply'
revision=26.2.6
mesa_hash=b9436b3e1a8be76fbd4823dc884f90596ab7c6ac5e1867a305e66ffccfb31a92
ndk_hash=59c2f6dc96743b5daf5d1626684640b20a6bd2b1d85b13156b90333741bad5cc
mesa_dir="$work_dir/mesa-$revision"
verified_download() {
 local url="$1" destination="$2" hash="$3" temp
 if [[ -f "$destination" ]] && echo "$hash  $destination" | sha256sum -c - --status; then return; fi
 temp="$(mktemp "$work_dir/download.XXXXXXXX")"
 if ! curl --fail --location --retry 3 --connect-timeout 30 --output "$temp" "$url"; then rm -f "$temp"; return 1; fi
 if ! echo "$hash  $temp" | sha256sum -c -; then rm -f "$temp"; return 1; fi
 mv -f "$temp" "$destination"
}
if [[ ! -d "$mesa_dir" ]]; then
 verified_download "https://archive.mesa3d.org/mesa-$revision.tar.xz" "$work_dir/mesa.tar.xz" "$mesa_hash"
 tar -xJf "$work_dir/mesa.tar.xz" -C "$work_dir"
fi
[[ -f "$mesa_dir/VERSION" ]] || { echo 'Incomplete Mesa source' >&2; exit 1; }
if [[ -z "${ANDROID_NDK_HOME:-}" ]]; then
 ANDROID_NDK_HOME="$work_dir/android-ndk-r27c"
 if [[ ! -f "$ANDROID_NDK_HOME/source.properties" ]]; then
  verified_download 'https://dl.google.com/android/repository/android-ndk-r27c-linux.zip' "$work_dir/ndk.zip" "$ndk_hash"
  unzip -q "$work_dir/ndk.zip" -d "$work_dir"
 fi
fi
export ANDROID_NDK_HOME
[[ -f "$ANDROID_NDK_HOME/source.properties" ]] || { echo 'Incomplete NDK' >&2; exit 1; }
grep -q 'Pkg.Revision = 27.2.12479018' "$ANDROID_NDK_HOME/source.properties" || { echo 'Wrong NDK revision' >&2; exit 1; }
version="$(cat "$mesa_dir/VERSION")"
[[ "$version" == '26.2.6' ]] || { echo "Unexpected Mesa version: $version" >&2; exit 1; }
# Mesa 26.2.6 includes upstream Turnip/A650 hang workarounds and bug fixes.
# Do NOT apply the Mesa 27 patches: their context and ownership may have changed.
# Always assert patched paths, including when restoring a cached work directory.
python3 "$recipe_dir/tests/test_source.py" "$mesa_dir"
python3 "$recipe_dir/test_toolchain.py" "$ANDROID_NDK_HOME"
python3 "$recipe_dir/build_exp18.py" "$mesa_dir" "$ANDROID_NDK_HOME" "$work_dir/out"
python3 "$recipe_dir/pack_driver.py" "$work_dir/out/src/freedreno/vulkan/libvulkan_freedreno.so" \
 "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" \
 "$work_dir/Turnip_A650_EXP19_MESA_26_2_6.zip"
python3 "$recipe_dir/tests/test_package.py" "$work_dir/Turnip_A650_EXP19_MESA_26_2_6.zip"
