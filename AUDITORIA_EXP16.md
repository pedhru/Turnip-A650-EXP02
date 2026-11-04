# Auditoria Turnip A650 EXP16

## Erro confirmado pela execução do GitHub

- Execução: https://github.com/pedhru/Turnip-A650-EXP02/actions/runs/41759402735/job/126343286296
- Versão: EXP15 / Mesa 27.0.0-devel / A650 KGSL / Android 13 / NDK r28c
- Falha: `src/freedreno/vulkan/tu_buffer.cc:138:25` com `[-Wc++11-narrowing]`; `.memoryTypeBits` inicializada com expressão de tipo `int` em campo `uint32_t`.
- Progresso anterior: falhou no alvo de compilação ~861/901.
- Diagnósticos: coleta de logs funcionando, artifact 13290365518.

## Correção EXP16

- `tools/fix_mesa_narrowing.py`: sétimo local, modificação explícita e idempotente, com falha em código incompatível.
- O cálculo da máscara passa a usar `1u` e trata `>= 32` como `UINT32_MAX`, evitando shift de 32 bits; em Vulkan, `memoryTypeBits` é uma máscara de 32 bits.
- `tests/test_compiler_compat.py`: casos 0,1,31,32,33 no compilador C++17, repetição, incompatibilidade de fonte.
- `build_turnip.sh`: `ninja -k 0` continua nos targets independentes para coletar mais erros por execução, mantendo status de falha pelo `pipefail`.
- Compilação real ainda pendente. As correções anteriores para LRZ, command stream e BVH foram mantidas.

## Riscos

- O Mesa `main` é móvel; outras incompatibilidades podem surgir.
- Não é seguro inferir ganhos de FPS ou Vulkan 1.4 sem validação física no Edge 20 Pro.
- Não se altera o driver original do sistema; ZIP destinado ao carregamento por app compatível.
