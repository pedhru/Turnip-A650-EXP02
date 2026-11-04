# Turnip A650 EXP13 | Mesa/Android KGSL AutoBuilder

Este arquivo contém **código para compilar** um driver Turnip, NÃO uma biblioteca `.so` pronta.
O pacote é voltado ao **Motorola Edge 20 Pro, Adreno 650, Android 13 (API 33), ARM64**.

## Auditoria EXP12 → EXP13 (após log real do GitHub Actions)

- **Causa raiz corrigida**: `meson setup "$build" "$MESA_DIR"` agora informa explicitamente o diretório fonte (antes só passava `$build`).
- `compile_driver()` verifica a existência de `meson.build` e `VERSION` antes de configurar.
- **3 testes de integração Bash** executam a função real com um Meson simulado, cobrindo caminho fonte, falha antecipada e carregamento sem efeitos colaterais.
- O checkout e a verificação de patches agora vêm **antes** do download do NDK, reduzindo desperdício quando a fonte ou o patch falham.
- Pacote de driver continua exigindo validação ELF/ZIP/dependências; compilação física e testes de GPU permanecem pendentes.

## Recursos preservados do EXP12

- Usa o **repositório oficial do Mesa** (`gitlab.freedesktop.org/mesa/mesa.git`). O commit exato aparece no nome do ZIP e no `*.build.json`; `mesa_ref` também aceita SHA fixo para repetir uma compilação.
- **Dois perfis seguros e explícitos**: `baseline` (recomendado, código do upstream, sem patches) e `exp02` (aplica `mesa-exp02.patch` **apenas** se `git apply --check` aprovar). Nada é ignorado silenciosamente.
- Não ativa por engano patches antigos de Adreno 8xx/Wayland/Linux no alvo A650. Os arquivos de patch históricos continuam disponíveis na pasta `patches/`, mas são **legado não aplicado**.
- NDK r28c (r27c opcional), Android API 33, compilação KGSL/Turnip com Meson, Ninja, opções de cache de shader ativadas e erros de compilação não ocultados por `-Wno-error` genérico.
- Validação do pacote: ZIP exato, `meta.json`, SHA-256, ELF compartilhado AArch64 de 64 bits e ausência de dependência direta de `libdrm.so` (inspeção com `readelf`).
- Artefatos trazem `*.zip`, `*.zip.sha256` e `*.zip.build.json`, com revisão do Mesa, patch, NDK e demais parâmetros.
- Testes automáticos Python e inspeção de logs ADB sem root.

**Não** significa Vulkan 1.4 habilitado, desempenho melhorado ou compatibilidade garantida. Essas informações exigem teste real no aparelho. Compilar Turnip não implementa funcionalidades ausentes na GPU e não resolve automaticamente bugs do Eden EXP05.

## Como usar pelo GitHub (recomendado)

1. Coloque o conteúdo inteiro deste ZIP na raiz do repositório GitHub. Preserve a pasta `.github/workflows/`.
2. Faça commit na branch principal. Como alternativa, usando Git em um PC: `git add . && git commit -m 'Turnip A650 EXP13' && git push`.
3. Abra **Actions → Turnip A650 EXP13 - Android KGSL verified → Run workflow**.
4. Em `mesa_ref`, use `main` para uma build do Mesa mais recente no momento da execução. Para comparar drivers, **reutilize o SHA mostrado no relatório da primeira build**.
5. Selecione `baseline`; mantenha `vulkan_beta = false` inicialmente. Execute. O workflow primeiro roda testes locais e depois compila no servidor Linux.
6. Baixe o artefato **Turnip-A650-EXP13-baseline**. Dentro dele estará o ZIP para importar no gerenciador de drivers do Eden, sem extrair o ZIP interno. Guarde o `.sha256` e o `.build.json`.
7. Faça o teste com um jogo, preserve os logs e compare na **mesma versão do Eden, com as mesmas opções de resolução, cache e configurações**.

### Testar o patch EXP02

Selecione `profile = exp02` e fixe o **mesmo** `mesa_ref`/SHA da baseline. O histórico `mesa-exp02.patch` pode não se aplicar em Mesa moderno e pode provocar regressões. O build é abortado se o patch não aplicar: não usamos `patch --fuzz`, sed de substituição nem rollback silencioso.

### Verificações locais (Linux)

```bash
bash -n build_turnip.sh
python3 -m unittest discover -s tests -v
```

### Compilar localmente (Linux x86_64)

Instale `git curl unzip zip meson ninja python3 flex bison glslangValidator pkg-config readelf cc c++` e `mako`, `pyyaml`, `packaging` para Python. Depois:

```bash
MESA_REF=main PATCH_PROFILE=baseline NDK_VERSION=r28c ANDROID_API=33 bash build_turnip.sh
```

O Termux **não compila** este projeto diretamente: a compilação foi preparada para Linux x86_64 e roda remotamente nos GitHub Actions. O celular pode ser usado para subir arquivos e baixar o resultado.

## Teste de dispositivo (com ADB autorizado)

Em um PC/Linux conectado ao telefone por ADB, jogue, reproduza o erro e depois execute:

```bash
bash tools/collect_adb.sh ./logs-a650-baseline
python3 tools/analyze_log.py ./logs-a650-baseline/filtered-logcat.txt --json
```

Essa coleta não exige root nem limpa o logcat. **Revise e remova dados privados** antes de compartilhar. Ela só identifica mensagens suspeitas (`VK_ERROR_DEVICE_LOST`, KGSL, sinais fatais). Não detecta qualidade visual nem prova a causa do crash. Execute o mesmo procedimento com o driver EXP02 para comparar.

## Importante: limites de validação

- **Validado localmente**: sintaxe de Bash/Python, testes unitários do empacotamento, rejeição de arquivos inválidos, integridade de arquivos no pacote-fonte.
- **Pendente**: compilação completa Mesa/NDK no GitHub; carregamento pela libadrenotools no Eden; testes físicos de Vulkan, FPS, estabilidade, consumo de bateria e compatibilidade com jogos.
- Patches de outras gerações não são apropriados para Adreno 650 por padrão. Em especial, não selecione patches A8xx para tentar ganhar desempenho em A650.

Referências:
- Mesa Android: https://docs.mesa3d.org/android
- Mesa fonte oficial: https://docs.mesa3d.org/repository.html
- Formato ADPKG: https://github.com/bylaws/libadrenotools/blob/master/tools/ADPKG.md
