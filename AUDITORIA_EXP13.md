# Auditoria técnica: EXP12 → EXP13

## Falha observada (log GitHub Actions)

- NDK r28c baixado e extraído corretamente.
- Mesa `27.0.0-devel`, SHA `98a55f454dff645be1c88284634126a2c17fd416`, obtido corretamente.
- `meson setup "$build"` não recebeu `"$MESA_DIR"`. Como o shell estava no repositório do construtor, o Meson não encontrou `meson.build`.
- Build interrompido antes de compilar a biblioteca. **Não é evidência de falha de driver ou GPU.**

## Correções implementadas

1. Passagem explícita do diretório de código-fonte ao `meson setup`.
2. Verificação de `meson.build` e `VERSION` antes de chamar Meson.
3. Check-out de fonte e verificação de patch antes do grande download do NDK.
4. `main` só é executado ao invocar `build_turnip.sh` diretamente, habilitando testes da função real.
5. Novo teste simulando Meson: diretório fonte correto, fonte ausente e importação sem efeitos colaterais.
6. Workflow EXP13 mantém saída (ADPKG ZIP, SHA-256 e proveniência) e validação de ELF ARM64.

## Limites / riscos residuais

- Compilação completa de Mesa 27 com NDK r28c e compatibilidade real no telefone ainda **não verificadas**. Próximos logs podem mostrar erros de Meson, dependências ou C/C++.
- Mesa `main` é referência móvel. O commit completo é registrado no artefato para permitir nova compilação.
- Patch `exp02` é legado e pode falhar ao aplicar; patches A8xx ficam desativados.
- CI não valida FPS, ausência de artefatos gráficos, estabilidade ou versão Vulkan real da GPU.
