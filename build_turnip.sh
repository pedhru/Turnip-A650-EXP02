#!/usr/bin/env bash
# Turnip A650 EXP13: audited Android/KGSL builder (Meson source path fixed).
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${WORKDIR:-$ROOT/.work}"
OUT_DIR="${OUT_DIR:-$ROOT/dist}"
NDK_VERSION="${NDK_VERSION:-r28c}"
ANDROID_API="${ANDROID_API:-33}"
MESA_REPO="${MESA_REPO:-https://gitlab.freedesktop.org/mesa/mesa.git}"
MESA_REF="${MESA_REF:-main}"
PATCH_PROFILE="${PATCH_PROFILE:-baseline}"
VARIANT_NAME="${VARIANT_NAME:-Turnip-A650-EXP13}"
BUILD_VERSION="${BUILD_VERSION:-1}"
VULKAN_BETA="${VULKAN_BETA:-false}"
JOBS="${JOBS:-2}"
NDK_ZIP_SHA256="${NDK_ZIP_SHA256:-}"

log() { printf '\n[EXP13] %s\n' "$*"; }
die() { printf '[EXP13] ERROR: %s\n' "$*" >&2; exit 1; }
trap 'printf "[EXP13] FAILURE at line %s: %s\n" "$LINENO" "$BASH_COMMAND" >&2' ERR

validate_input() {
    [[ "$NDK_VERSION" =~ ^r[0-9]+[a-z]?$ ]] || die 'Invalid NDK_VERSION'
    [[ "$ANDROID_API" =~ ^[0-9]+$ ]] && ((ANDROID_API >= 28 && ANDROID_API <= 36)) || die 'ANDROID_API must be between 28 and 36'
    [[ "$JOBS" =~ ^[0-9]+$ ]] && ((JOBS >= 1 && JOBS <= 16)) || die 'JOBS must be 1..16'
    [[ "$BUILD_VERSION" =~ ^[A-Za-z0-9._-]+$ ]] || die 'Invalid BUILD_VERSION'
    [[ "$VARIANT_NAME" =~ ^[A-Za-z0-9._-]+$ ]] || die 'VARIANT_NAME supports ASCII letters, digits, dot, dash, underscore'
    [[ "$VULKAN_BETA" == true || "$VULKAN_BETA" == false ]] || die 'VULKAN_BETA must be true or false'
    [[ "$MESA_REF" =~ ^[A-Za-z0-9._/-]+$ ]] && [[ "$MESA_REF" != -* ]] && [[ "$MESA_REF" != */../* ]] || die 'Invalid MESA_REF'
    case "$PATCH_PROFILE" in baseline|exp02) ;; *) die 'PATCH_PROFILE must be baseline or exp02' ;; esac
    case "$MESA_REPO" in
        https://gitlab.freedesktop.org/mesa/mesa.git|https://github.com/mirror/mesa.git) ;;
        *) die 'Untrusted MESA_REPO; supported official repository or known mirror only' ;;
    esac
    case "$(uname -s)/$(uname -m)" in Linux/x86_64|Linux/amd64) ;; *) die 'This build requires Linux x86_64 (GitHub Actions)' ;; esac
}

require_deps() {
    local d
    for d in git curl unzip zip meson ninja python3 flex bison glslangValidator pkg-config readelf sha256sum cc c++; do
        command -v "$d" >/dev/null || die "Missing dependency: $d"
    done
    python3 -c 'import mako, yaml, packaging' >/dev/null || die 'Missing Python modules: mako, pyyaml, packaging'
}

prepare_ndk() {
    local n="android-ndk-$NDK_VERSION"
    local archive="$WORKDIR/$n-linux.zip"
    local ndk_dir="$WORKDIR/$n"
    NDK_BIN="$ndk_dir/toolchains/llvm/prebuilt/linux-x86_64/bin"
    if [[ ! -x "$NDK_BIN/aarch64-linux-android${ANDROID_API}-clang" ]]; then
        log "Downloading official Android NDK $NDK_VERSION"
        mkdir -p "$WORKDIR"
        curl --fail --location --retry 3 --retry-delay 3 --output "$archive.tmp" \
            "https://dl.google.com/android/repository/$n-linux.zip"
        mv "$archive.tmp" "$archive"
        if [[ -n "$NDK_ZIP_SHA256" ]]; then
            printf '%s  %s\n' "$NDK_ZIP_SHA256" "$archive" | sha256sum -c -
        fi
        unzip -tqq "$archive" || die 'Corrupt NDK archive'
        unzip -q -o "$archive" -d "$WORKDIR"
        rm -f "$archive"
    fi
    [[ -x "$NDK_BIN/aarch64-linux-android${ANDROID_API}-clang" ]] || die 'NDK compiler missing'
    [[ -x "$NDK_BIN/llvm-readelf" ]] || die 'NDK llvm-readelf missing'
    [[ -x "$NDK_BIN/llvm-strip" ]] || die 'NDK llvm-strip missing'
    NDK_REVISION="$(sed -n 's/^Pkg.Revision *= *//p' "$ndk_dir/source.properties" | head -n1)"
    log "NDK revision $NDK_REVISION; target Android API $ANDROID_API"
}

fetch_source() {
    MESA_DIR="$WORKDIR/mesa-src"
    rm -rf "$MESA_DIR"
    mkdir -p "$MESA_DIR"
    git -C "$MESA_DIR" init -q
    git -C "$MESA_DIR" remote add origin "$MESA_REPO"
    log "Fetching Mesa ref $MESA_REF"
    if ! git -C "$MESA_DIR" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=90 \
        fetch --no-tags --depth=1 origin "$MESA_REF"; then
        if [[ "$MESA_REPO" == 'https://gitlab.freedesktop.org/mesa/mesa.git' ]]; then
            log 'Official Mesa GitLab unavailable; trying the public GitHub mirror'
            MESA_REPO='https://github.com/mirror/mesa.git'
            git -C "$MESA_DIR" remote set-url origin "$MESA_REPO"
            git -C "$MESA_DIR" fetch --no-tags --depth=1 origin "$MESA_REF" \
                || die 'Mesa fetch failed on both primary and mirror'
        else
            die 'Mesa fetch failed'
        fi
    fi
    git -C "$MESA_DIR" -c advice.detachedHead=false checkout -q FETCH_HEAD
    [[ -f "$MESA_DIR/meson.build" && -f "$MESA_DIR/VERSION" ]] || die 'Not a Mesa source tree'
    MESA_SHA="$(git -C "$MESA_DIR" rev-parse HEAD)"
    MESA_VERSION="$(tr -d '[:space:]' < "$MESA_DIR/VERSION")"
    log "Resolved Mesa $MESA_VERSION, commit $MESA_SHA"
}

apply_selected_patches() {
    PATCH_FILE=''
    PATCH_SHA='none'
    case "$PATCH_PROFILE" in
        baseline)
            log 'Baseline profile: no code patches (KGSL from upstream)'
            ;;
        exp02)
            PATCH_FILE="$ROOT/mesa-exp02.patch"
            [[ -s "$PATCH_FILE" ]] || die 'EXP02 patch missing'
            PATCH_SHA="$(sha256sum "$PATCH_FILE" | cut -d' ' -f1)"
            log 'Checking EXP02 patch against this exact Mesa revision'
            if ! git -C "$MESA_DIR" apply --check --verbose "$PATCH_FILE"; then
                die 'EXP02 patch incompatible with selected Mesa. No driver is packaged.'
            fi
            git -C "$MESA_DIR" apply "$PATCH_FILE"
            git -C "$MESA_DIR" diff --check || die 'Patch introduced whitespace errors'
            ;;
    esac
}

make_cross_file() {
    mkdir -p "$WORKDIR"
    CROSS_FILE="$WORKDIR/android-aarch64.ini"
    cat > "$CROSS_FILE" <<CROSS
[binaries]
ar = '$NDK_BIN/llvm-ar'
c = '$NDK_BIN/aarch64-linux-android${ANDROID_API}-clang'
cpp = ['$NDK_BIN/aarch64-linux-android${ANDROID_API}-clang++', '-fno-exceptions', '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-static-libstdc++']
c_ld = '$NDK_BIN/ld.lld'
cpp_ld = '$NDK_BIN/ld.lld'
strip = '$NDK_BIN/llvm-strip'
pkg-config = ['env', 'PKG_CONFIG_LIBDIR=/nonexistent', '$(command -v pkg-config)']

[host_machine]
system = 'android'
cpu_family = 'aarch64'
cpu = 'armv8'
endian = 'little'
CROSS
}

compile_driver() {
    local build="$WORKDIR/build-a650-$PATCH_PROFILE"
    INSTALL_DIR="$WORKDIR/install-a650-$PATCH_PROFILE"
    rm -rf "$build" "$INSTALL_DIR"
    [[ -f "$MESA_DIR/meson.build" && -f "$MESA_DIR/VERSION" ]] || die "Mesa source directory invalid: $MESA_DIR"
    log 'Configuring Mesa with Android/KGSL, Freedreno Vulkan and shader cache'
    # Explicit source directory is essential when invoked outside the Mesa tree.
    meson setup "$build" "$MESA_DIR" \
        --cross-file "$CROSS_FILE" \
        --prefix "$INSTALL_DIR" \
        -Dbuildtype=release \
        -Dstrip=true \
        -Dplatforms=android \
        -Dplatform-sdk-version="$ANDROID_API" \
        -Dandroid-stub=true \
        -Dandroid-libbacktrace=disabled \
        -Dgallium-drivers= \
        -Dvideo-codecs= \
        -Dvulkan-drivers=freedreno \
        -Dvulkan-beta="$VULKAN_BETA" \
        -Dfreedreno-kmds=kgsl \
        -Dshader-cache=enabled \
        -Degl=disabled
    log "Compiling using $JOBS jobs"
    meson compile -C "$build" -j "$JOBS"
    meson install -C "$build"
    LIBRARY="$(find "$INSTALL_DIR" -type f -name libvulkan_freedreno.so -print -quit)"
    [[ -n "$LIBRARY" && -s "$LIBRARY" ]] || die 'Installed Turnip .so not found'
}

package_driver() {
    mkdir -p "$OUT_DIR"
    local stem="$VARIANT_NAME-$PATCH_PROFILE-${MESA_SHA:0:10}-run${BUILD_VERSION}"
    ZIP_PATH="$OUT_DIR/$stem.zip"
    python3 "$ROOT/tools/package_driver.py" \
        --library "$LIBRARY" --output "$ZIP_PATH" \
        --name "$VARIANT_NAME-$PATCH_PROFILE" \
        --driver-version "Mesa $MESA_VERSION-${MESA_SHA:0:10}" \
        --description "Turnip A650 KGSL / Mesa $MESA_VERSION / $PATCH_PROFILE / NDK $NDK_VERSION" \
        --package-version "$BUILD_VERSION" --min-api "$ANDROID_API" \
        --author 'Turnip A650 EXP12 community build'
    python3 "$ROOT/tools/validate_driver.py" "$ZIP_PATH" --readelf "$NDK_BIN/llvm-readelf"
    SHA256="$(sha256sum "$ZIP_PATH" | cut -d' ' -f1)"
    printf '%s  %s\n' "$SHA256" "$(basename "$ZIP_PATH")" > "$ZIP_PATH.sha256"
    export MESA_SHA MESA_VERSION MESA_REPO MESA_REF PATCH_PROFILE PATCH_SHA NDK_VERSION NDK_REVISION ANDROID_API VULKAN_BETA VARIANT_NAME BUILD_VERSION ZIP_PATH SHA256
    python3 "$ROOT/tools/build_report.py" --output "$ZIP_PATH.build.json"
    log "Build finished: $ZIP_PATH"
    log "SHA256: $SHA256"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
        {
            echo "driver_zip=$ZIP_PATH"
            echo "driver_name=$(basename "$ZIP_PATH")"
            echo "mesa_sha=$MESA_SHA"
        } >> "$GITHUB_OUTPUT"
    fi
}

main() {
    validate_input
    require_deps
    mkdir -p "$WORKDIR" "$OUT_DIR"
    # Resolve source and patch compatibility before downloading the ~688 MB NDK.
    fetch_source
    apply_selected_patches
    prepare_ndk
    make_cross_file
    compile_driver
    package_driver
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
