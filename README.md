# Turnip A650 EXP15 | Android 13 / ARM64 / KGSL

Atualização pontual do EXP14 com base no [erro do GitHub Actions run 41755947921](https://github.com/pedhru/Turnip-A650-EXP02/actions/runs/41755947921/job/126332012239).

## O que mudou

- EXP14 corrigiu os quatro erros de narrowing anteriores, mas a compilação parou no arquivo `tu_acceleration_structure.cc` em duas inicializações de offsets BVH.
- EXP15 acrescenta `uint32_t` explícito exatamente nessas duas posições, reproduzindo a conversão de destino, sem desativar os avisos do compilador.
- O script de compatibilidade agora recusa alterações upstream inesperadas em vez de ignorá-las em silêncio. É idempotente, com registros de hash SHA-256.
- O workflow passa a anexar os diagnósticos de `.work` com `include-hidden-files: true` se a build falhar.

## Como compilar

Rode os testes locais (não compilam o Mesa):

```bash
bash -n build_turnip.sh
python3 -m unittest discover -s tests -v
```

No repositório GitHub use **Actions → Turnip A650 EXP15 → Run workflow**:

- `profile=baseline`
- `mesa_ref=main` (ou SHA `98a55f454dff645be1c88284634126a2c17fd416` para tentar reproduzir o código exato)
- `compiler_fixes=true`
- `ndk=r28c`
- `vulkan_beta=false`

Também é possível usar o instalador automático para Termux ou Linux/PROOT que acompanha a distribuição. Nenhum driver binário está incluso neste projeto. Para detalhes veja `AUDITORIA_EXP15.md`.

**Atenção:** conversões para 32 bits podem truncar valores grandes. A build estática não demonstra compatibilidade ou desempenho na GPU Adreno 650.
