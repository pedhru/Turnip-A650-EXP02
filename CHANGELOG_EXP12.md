# EXP11 → EXP12: registro técnico

## Corrigido

1. **Referência Mesa**: EXP11 fazia clone de `main`, então builds sucessivas eram difíceis de comparar. EXP12 resolve o SHA completo, aceita commit fixo, identifica a revisão no nome do ZIP e em relatório de proveniência.
2. **Compilação Android**: API 30 no EXP11 foi alinhada ao dispositivo Android 13/API 33. O NDK padrão passou a r28c (r27c opcional). Removidos flags genéricos para suprimir erros de compilação; Cross-file usa clang do NDK com STL C++ estática.
3. **Segurança de patch**: no EXP11, `EXTRA_PATCH`/`EXTRA_SCRIPT` sem arquivo eram silenciosamente ignorados e um script Python podia redefinir arquivos Mesa após erros. EXP12 aceita somente perfis explícitos, usa `git apply --check` e falha antes de compilar se houver conflito.
4. **Isolamento A650**: EXP11 misturava patches de A8xx, Wayland e Linux e tinha assertivas upstream muito específicas; no EXP12 o perfil padrão é Mesa upstream puro para A650. As correções históricas foram preservadas, mas não aplicadas.
5. **Driver ZIP**: os metadados são gerados por JSON Python, com validação real da arquitetura ELF AArch64, tipo ET_DYN, `meta.json`, `readelf` das dependências, integridade ZIP, limites de tamanho e hash SHA-256.
6. **CI**: separação de testes de ferramentas e build, cache NDK, relatórios, upload de ZIP, SHA e proveniência, sem indicar sucesso de Vulkan 1.4 ou performance sem testes.
7. **Comparação no celular**: scripts de coleta ADB e classificação heurística de crashes de Vulkan/Turnip, com alerta sobre privacidade.

## Escopo

- **12 testes unitários locais aprovados**; Bash sintaticamente válido; workflow YAML analisado.
- **Não realizado aqui**: download do Mesa/NDK, build nativo, instalação no Eden, benchmarks FPS ou ensaio real de compatibilidade no Adreno 650.
- **EXP02**: `mesa-exp02.patch` preservado como experimental; pode falhar em Mesa atual, por mudanças de contexto ou por incompatibilidade semântica.

## Arquivos adicionados

- `tools/package_driver.py`, `tools/validate_driver.py`, `tools/build_report.py`
- `tools/collect_adb.sh`, `tools/analyze_log.py`
- `tests/test_packages.py`, `tests/test_log.py`
- `CHANGELOG_EXP12.md`

Arquivos modificados: `README.md`, `build_turnip.sh`, `.github/workflows/build_a650.yml`.
