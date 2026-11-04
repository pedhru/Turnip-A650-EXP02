# Auditoria EXP15 do Turnip A650 / Android KGSL

## Evidência confirmada

- Workflow: https://github.com/pedhru/Turnip-A650-EXP02/actions/runs/41755947921/job/126332012239
- Mesa 27.0.0-devel, commit `98a55f454dff645be1c88284634126a2c17fd416`.
- As quatro correções do EXP14 removeram os erros anteriores de `tu_cs.h` e `freedreno_lrz_layout.h`.
- **Novo erro em** `src/freedreno/vulkan/tu_acceleration_structure.cc`, linhas 203 e 255: conversões de `uint64_t` para `uint32_t` nas inicializações `.output_bvh_offset` e `.bvh_offset`.
- O Clang C++17 rejeitou as inicializações estreitadoras `[-Wc++11-narrowing]`, em `tu_acceleration_structure.cc.o` por volta da etapa 859/901.
- O upload dos logs foi ignorado porque `.work` é um diretório oculto; `actions/upload-artifact@v4` precisa de `include-hidden-files: true`.

## Alterações EXP15

1. `tools/fix_mesa_narrowing.py`: duas conversões explícitas `uint32_t` adicionais com correspondência textual exata; continua idempotente e registra hashes antes/depois.
2. Fail-closed se nenhuma das formas (original/corrigida) for encontrada no Mesa, em vez de supor compatibilidade com código fonte desconhecido.
3. `tests/test_compiler_compat.py`: testa as 6 conversões, execução repetida, dry run, ambiguidades, fonte inesperada e compilação sintática C/C++.
4. `.github/workflows/build_a650.yml`: `include-hidden-files: true` na etapa de diagnósticos, para anexar logs `.work` na falha.
5. `build_turnip.sh`: identificação EXP15 e proveniência preservada.

## Limites

- Os casts preservam uma conversão para 32 bits que pode truncar se o valor exceder `UINT32_MAX`; não são uma correção de overflow ou uma prova da correção funcional.
- Testes sintéticos locais não substituem a compilação Mesa/NDK completa ou testes de emulação no Edge 20 Pro.
- O Mesa `main` muda com o tempo. Para reproduzir exatamente a origem analisada, utilize o commit completo acima se ele estiver acessível por fetch Git.
