"""Smoke tests for the real Bash build function, using a fake Meson executable.

They catch the EXP12 regression before GitHub downloads the NDK.
These DO NOT build Mesa or validate GPU execution.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "mesa-src").mkdir()
        (self.root / "mesa-src/meson.build").write_text("project('test', 'c')\n")
        (self.root / "mesa-src/VERSION").write_text("27.0.0-devel\n")
        (self.root / "work").mkdir()
        (self.root / "cross.ini").write_text("[host_machine]\nsystem = 'android'\n")

    def run_shell(self, code: str, check=True):
        env = dict(os.environ, SCRIPT=str(ROOT / 'build_turnip.sh'), MOCK_DIR=str(self.root))
        return subprocess.run(['bash', '-c', code], env=env, text=True,
                              capture_output=True, check=check)

    def test_meson_receives_source_and_build_dir(self):
        result = self.run_shell(r'''
            source "$SCRIPT"
            MESA_DIR="$MOCK_DIR/mesa-src"
            WORKDIR="$MOCK_DIR/work"
            CROSS_FILE="$MOCK_DIR/cross.ini"
            PATCH_PROFILE=baseline
            JOBS=2
            ANDROID_API=33
            VULKAN_BETA=false
            meson() {
                case "$1" in
                  setup)
                    [[ "$2" == "$WORKDIR/build-a650-baseline" ]] || return 31
                    [[ "$3" == "$MESA_DIR" ]] || return 32
                    [[ -f "$3/meson.build" ]] || return 33
                    ;;
                  compile) [[ "$2" == -C ]] || return 34 ;;
                  install)
                    mkdir -p "$INSTALL_DIR/lib"
                    printf 'mock ELF, not a real driver' > "$INSTALL_DIR/lib/libvulkan_freedreno.so"
                    ;;
                  *) return 35 ;;
                esac
            }
            compile_driver
            [[ -s "$LIBRARY" ]]
        ''')
        self.assertIn('Configuring Mesa', result.stdout)

    def test_missing_source_fails_before_meson(self):
        result = self.run_shell(r'''
            source "$SCRIPT"
            MESA_DIR="$MOCK_DIR/nonexistent"
            WORKDIR="$MOCK_DIR/work"
            CROSS_FILE="$MOCK_DIR/cross.ini"
            PATCH_PROFILE=baseline
            ANDROID_API=33
            VULKAN_BETA=false
            meson() { echo 'MESON SHOULD NOT RUN'; return 90; }
            compile_driver
        ''', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Mesa source directory invalid', result.stderr)
        self.assertNotIn('MESON SHOULD NOT RUN', result.stdout)

    def test_source_is_safe_to_import_without_executing_main(self):
        result = self.run_shell('source "$SCRIPT"; echo SOURCE_OK')
        self.assertEqual(result.stdout.strip(), 'SOURCE_OK')

if __name__ == '__main__':
    unittest.main()
