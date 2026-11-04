# EXP14 audit: GitHub run 41748637122

- GitHub job 126307928227: static check job succeeded, build job failed.
- Mesa commit: `98a55f454dff645be1c88284634126a2c17fd416` (Mesa 27.0.0-devel).
- Ninja reached ~858/901 tasks. Errors in generated `tu_tracepoints.cc` compilation and `layers_tu_rmv_layer.cc`, both of which include the headers implicated below.
- Errors: `tu_cs.h:295,341` (`uint16_t` narrowing); `freedreno_lrz_layout.h:272,273` (`uint32_t` narrowing). No linker failure was reached.
- EXP14 introduces targeted explicit C-compatible casts to those four sites. Reproducibility is tracked in `*.compat.json` and `*.build.json`.
- Compiler behavior on the Mesa source must be retested on GitHub. Real GPU execution remains untested.
