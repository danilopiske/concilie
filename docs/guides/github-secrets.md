# GitHub Secrets — Guia de Configuração

> Repositório: `danilopiske/concilie`

## Como configurar um secret

1. Acesse **Settings → Secrets and variables → Actions** no repositório GitHub
2. Clique em **New repository secret**
3. Preencha **Name** e **Secret** conforme a tabela abaixo
4. Clique em **Add secret**

---

## Secrets necessários

### CI/CD (obrigatório para o pipeline funcionar)

| Secret | Ambiente | Descrição | Exemplo de valor |
|--------|----------|-----------|-----------------|
| `SECRET_KEY_CI` | CI (`ci.yml`) | JWT secret para testes automatizados. Pode ser qualquer string ≥ 32 chars — não é a chave de produção. | `ci-test-secret-key-not-for-production-32chars` |

**Como gerar um valor seguro:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### Produção (configurar antes do primeiro deploy)

| Secret | Ambiente | Descrição |
|--------|----------|-----------|
| `SECRET_KEY` | Produção | JWT secret de produção. Gerar com o comando acima — nunca reutilizar o de CI. |
| `MYSQL_PASSWORD` | Produção | Senha do MySQL em produção. |
| `DATABASE_URL` | Produção | URL completa de conexão com o banco, ex: `mysql+pymysql://user:pass@host/db` |
| `ALLOWED_ORIGINS_STR` | Produção | Lista JSON de origens CORS permitidas, ex: `["https://app.concilie.com.br"]` |

---

## Verificação

Após configurar `SECRET_KEY_CI`, faça um push qualquer para a branch e confirme que o job **API — Lint & Tests (Python)** passa em verde no GitHub Actions.

Se o job falhar com erro de autenticação nos testes, verifique:
1. O nome do secret é exatamente `SECRET_KEY_CI` (case-sensitive)
2. O secret foi salvo no repositório correto (`danilopiske/concilie`)
3. O valor tem pelo menos 32 caracteres

---

## Referências

- Story 3.2 — Configuração de Ambientes
- Dívida técnica C-01 (`docs/technical-debt.md`)
- Workflow CI: `.github/workflows/ci.yml`
