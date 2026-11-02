# EXP01 baseline (from uploaded ZIP)

- libvulkan_freedreno.so: 15,589,448 bytes
- SHA256: `859139dfb83d22b0e1b3f628905e058f30f431655980a7f31eb4b3fa017e460c`
- Mesa source revision: `1558388535b109e4e77919fc2a6ba11fc7f058f2`
- Build: Meson 1.12.1, Ninja 1.13.2, NDK r27c, Android API 30, ARM64, KGSL, release, no LTO
- Meson flags: `-Dbuildtype=release -Dplatforms=android -Dplatform-sdk-version=30 -Dandroid-stub=true -Dandroid-libbacktrace=disabled -Degl=disabled -Dgallium-drivers= -Dvulkan-drivers=freedreno -Dfreedreno-kmds=kgsl -Dllvm=disabled -Dglx=disabled -Dgles1=disabled -Dgles2=disabled -Dopengl=false -Dzstd=disabled -Dexpat=disabled --wrap-mode=nofallback`
- Reported Vulkan version: 1.3. No on-device validation was provided.
