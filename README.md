# Turnip A650 EXP14 | Android 13 / KGSL / Adreno 650

An update to EXP13 based on the real GitHub Actions failure in run `41748637122`, job `126307928227`.

## Root cause and fix

EXP13 got through Meson setup and 858/901 compile steps. Clang C++17 stopped at 4 narrowing list-initialization sites:

- `src/freedreno/vulkan/tu_cs.h` (2 sites): `unsigned long` or `uint32_t` to `uint16_t`.
- `src/freedreno/fdl/freedreno_lrz_layout.h` (2 sites): `size_t` to `uint32_t`.

`tools/fix_mesa_narrowing.py` performs 4 **exact**, C/C++-compatible explicit casts, rather than globally disabling warnings. It aborts on missing files or duplicate ambiguous matches, logs original/new SHA256 values and prints a JSON report. The automated fix is applied **before** downloading the Android NDK. Its presence is recorded in build metadata. This is a compiler fix, NOT evidence of a performance benefit or a fix for integer overflow in the original driver.

If upstream Mesa already changed these exact expressions, the tool doesn't invent replacements. It reports zero matches for those sites, and the real compiler is authoritative.

## GitHub Actions

In **Actions → Turnip A650 EXP14 - Android KGSL + compiler compatibility → Run workflow** choose:

- `mesa_ref`: `main` (or commit `98a55f454dff645be1c88284634126a2c17fd416` to reproduce the original failed source, if fetchable)
- `profile`: `baseline`
- `vulkan_beta`: `false`
- `compiler_fixes`: `true` (recommended)
- `ndk`: `r28c`

Artifacts: driver ZIP + SHA256 + build provenance + compiler compatibility report. If compilation fails, the job attempts to upload `meson-log.txt` and the compatibility report for diagnosis.

## Local tests

```bash
bash -n build_turnip.sh
python3 -m unittest discover -s tests -v
```

A sample synthetic Mesa tree is used to test the four known substitutions and idempotency. **This is not a successful Mesa/NDK build**. Validate the GitHub run and physical device behavior separately.

## Supported platform and boundaries

The build is Linux x86_64 → Android ARM64, KGSL backend, Android API 33, NDK r28c, Mesa source. The bundled legacy Adreno 8xx patches remain unused. It targets the user's Adreno 650 configuration, but cannot guarantee any runtime Vulkan version, game compatibility or FPS without testing on the actual phone.

## Install using Termux/PROOT

Use the separate EXP14 offline-installer shell script. It imports this archive, runs tests, authenticates through `gh` in the local session, pushes to `pedhru/Turnip-A650-EXP02` and dispatches `build_a650.yml`. No passwords or tokens should be shared in chat.
