#!/usr/bin/env python3
"""Build the patched EXP18 tree. Usage: build_exp18.py MESA_SOURCE NDK_ROOT OUT_DIR."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

src, ndk, out = [Path(p).resolve() for p in sys.argv[1:4]]
out.mkdir(parents=True, exist_ok=True)
toolchain = ndk/'toolchains/llvm/prebuilt/linux-x86_64'
assert (src/'src/freedreno/vulkan/tu_knl_kgsl.cc').is_file()
assert (toolchain/'bin/aarch64-linux-android30-clang++').is_file(), 'NDK toolchain missing'
assert (src/'VERSION').read_text().strip() == '26.2.6'
pkgconf = shutil.which('pkg-config')
assert pkgconf, 'Install pkgconf or pkg-config and add it to PATH'
settings = out.parent / (out.name + '-settings')
settings.mkdir(exist_ok=True)
pc = settings/'pkgconfig'; pc.mkdir(exist_ok=True)
(pc/'zlib.pc').write_text('Name: zlib\nDescription: Android system zlib\nVersion: 1.2.13\nLibs: -lz\nCflags:\n')
cross = settings/'android-a650.ini'
cross.write_text(f'''[binaries]
c = '{toolchain}/bin/aarch64-linux-android30-clang'
cpp = '{toolchain}/bin/aarch64-linux-android30-clang++'
ar = '{toolchain}/bin/llvm-ar'
strip = '{toolchain}/bin/llvm-strip'
pkg-config = '{pkgconf}'
[host_machine]
system = 'android'
cpu_family = 'aarch64'
cpu = 'armv8-a'
endian = 'little'
[properties]
needs_exe_wrapper = true
[built-in options]
c_args = ['-march=armv8.2-a+dotprod', '-mtune=cortex-a77']
cpp_args = ['-march=armv8.2-a+dotprod', '-mtune=cortex-a77']
cpp_link_args = ['-static-libstdc++']
''')
options = ['-Dbuildtype=release', '-Dvideo-codecs=', '-Dshader-cache=enabled', '-Dvulkan-beta=false', '-Db_lto=false', '-Dplatforms=android', '-Dplatform-sdk-version=30',
           '-Dandroid-stub=true', '-Dandroid-libbacktrace=disabled', '-Degl=disabled', '-Dgallium-drivers=',
           '-Dvulkan-drivers=freedreno', '-Dfreedreno-kmds=kgsl', '-Dllvm=disabled', '-Dglx=disabled',
           '-Dgles1=disabled', '-Dgles2=disabled', '-Dopengl=false', '-Dzstd=disabled', '-Dexpat=disabled',
           '--wrap-mode=nofallback']
env = {**os.environ, 'PKG_CONFIG_LIBDIR': str(pc)}
cmd=['meson','setup',str(out),str(src),'--cross-file',str(cross),*options]
if (out/'meson-private/coredata.dat').exists(): cmd.insert(2,'--wipe')
subprocess.run(cmd,check=True,env=env)
subprocess.run(['ninja','-C',str(out),'-j','4','src/freedreno/vulkan/libvulkan_freedreno.so'],check=True,env=env)
print(out/'src/freedreno/vulkan/libvulkan_freedreno.so')
