#!/usr/bin/env python3
"""Reproduce the EXP16 Meson probe failure with the real NDK, then verify the fix."""
from pathlib import Path
import os,subprocess,sys,tempfile
ndk=Path(sys.argv[1]).resolve();compiler=ndk/'toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android30-clang++'
with tempfile.TemporaryDirectory() as d:
 root=Path(d);source=root/'src';source.mkdir()
 (source/'meson.build').write_text("""project('probe-regression', 'cpp', default_options: ['cpp_std=c++17'])
cpp = meson.get_compiler('cpp')
conf = configuration_data()
conf.set('NARROWING_SUPPORTED', cpp.has_argument('-Wno-c++11-narrowing') ? 'yes' : 'no')
configure_file(output: 'probe-result.txt', configuration: conf)
""")
 for broken in [True,False]:
  name='old' if broken else 'fixed';cross=root/(name+'.ini');out=root/name
  cpp=f"['{compiler}', '-static-libstdc++']" if broken else f"'{compiler}'"
  cross.write_text(f"""[binaries]
cpp = {cpp}
[host_machine]
system = 'android'
cpu_family = 'aarch64'
cpu = 'armv8-a'
endian = 'little'
[properties]
needs_exe_wrapper = true
[built-in options]
cpp_link_args = {[] if broken else ['-static-libstdc++']}
""")
  r=subprocess.run(['meson','setup',str(out),str(source),'--cross-file',str(cross)],text=True,capture_output=True)
  if r.returncode: print(r.stdout,r.stderr);raise RuntimeError('Probe configuration failed')
  result=(out/'probe-result.txt').read_text()
  assert ('NARROWING_SUPPORTED '+('no' if broken else 'yes')) in result,result
  log=(out/'meson-logs/meson-log.txt').read_text()
  if broken: assert "argument unused during compilation: '-static-libstdc++'" in log
  print(f'{name}: compiler flag probe = {"NO (reproduced EXP16 failure)" if broken else "YES (fixed)"}')
print('Real NDK + Meson regression passed. No GPU execution involved.')
