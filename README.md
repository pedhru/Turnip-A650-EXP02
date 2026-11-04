# Turnip A650 EXP19 — Mesa 26.2.6 (upstream stable)

This recipe **switches** from Mesa 27.0.0-devel to official Mesa **26.2.6**, released 2026-10-28. The verified upstream source SHA256 is `b9436b3e1a8be76fbd4823dc884f90596ab7c6ac5e1867a305e66ffccfb31a92`. Official notes: https://docs.mesa3d.org/relnotes/26.2.6.html

Mesa 26.2.6 includes upstream **[Turnip/A650] game hang workaround**, IR3 fixes, and A650 register fixes listed in the release notes. It does **not** apply older EXP19 patches written for the Mesa 27 tree. Doing that without source review could reintroduce memory corruption or fail compilation. The recipe retains Android NDK r27c, ELF ARM64/HMI validation and ZIP CRC + checksum validation.

## Run

Upload all files, including `.github/workflows`, into a **separate branch** in `pedhru/Turnip-A650-EXP02`. In GitHub Actions choose **Turnip A650 Mesa 26.2.6 - Build and Validate** and run it. Download the generated Turnip zip artifact on success. Do not import the source ZIP as a driver.

## Verification / limitations

This package is **source + CI recipe only**. The Mesa archive could not be retrieved in the authoring environment, and **the full Android cross-build has not run here**. Meson options may need changes for Mesa 26.2.6 and the workflow will stop visibly if it cannot build. Do not claim performance gains, Vulkan 1.4 exposure on A650, or zero crashes. A game crash can originate in the emulator NCE, memory handling or game code, beyond the GPU driver.

Retest Eden under identical game, resolution, settings, thermal state compared to EXP11, using the GitHub-built binary, and inspect logcat/tombstone if a crash occurs.
