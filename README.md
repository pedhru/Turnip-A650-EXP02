# Turnip A650 EXP02

Projeto experimental para Adreno 650 / Android ARM64 / KGSL.

## Referência EXP01
- Mesa: 27.0.0-devel
- Commit declarado no pacote: `1558388535b109e4e77919fc2a6ba11fc7f058f2`
- NDK: r27c, Android API 30
- Vulkan declarado: 1.3

## Objetivo
Reproduzir a compilação do EXP01 e investigar o suporte **real** ao Vulkan 1.4. Não alterar `apiVersion` artificialmente. Uma compilação bem-sucedida não comprova conformidade Vulkan 1.4.

## Uso
1. Faça upload dos arquivos deste pacote na raiz do repositório, mantendo `.github/workflows/`.
2. Abra **Actions > Mesa source audit > Run workflow**.
3. Consulte o log e o artefato de auditoria.

O fluxo inicial só obtém e inspeciona o código-fonte; **não compila nem distribui um driver**. Isso evita apresentar um binário não testado como Vulkan 1.4.

Fonte upstream: https://gitlab.freedesktop.org/mesa/mesa
