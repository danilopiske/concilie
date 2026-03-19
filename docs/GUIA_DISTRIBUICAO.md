# Guia de Distribuição e Build

Este guia descreve o processo técnico para empacotar o sistema **Concilie** em um executável standalone (`.exe`) para Windows, permitindo a distribuição para clientes sem a necessidade de instalação manual de Python ou Node.js.

---

## 🛠️ Pré-requisitos de Build

Para gerar a distribuição, o ambiente de desenvolvimento deve ter as seguintes ferramentas instaladas e configuradas:

1.  **Python 3.11+**: Com gerenciador de pacotes `pip`.
2.  **Poetry**: Para gestão de dependências do Python.
3.  **Node.js 18+ & pnpm**: Para build do frontend Next.js.
4.  **PyInstaller**: Ferramenta de congelamento de código (instalada via Poetry).

## 📦 Processo de Build Automatizado

O projeto conta com um script automatizado `build_dist.py` que orquestra todo o processo.

### Passo 1: Preparar o Ambiente

Certifique-se de que todas as dependências estão atualizadas:

```powershell
# Atualizar dependências Python
poetry install

# Atualizar dependências Frontend
cd apps/web
pnpm install
```

### Passo 2: Executar o Script de Build

Na raiz do projeto, execute o script:

```powershell
python build_dist.py
```

### O que o script faz?

1.  **Limpeza**: Remove builds anteriores (`dist_v18`, `apps/web/out`).
2.  **Build Frontend**: Executa `pnpm run build` no Next.js, gerando arquivos estáticos em `apps/web/out` (modo export).
3.  **Coleta de Assets**: Copia configurações (`conf`), banco semente (`data/concilie.db`) e módulos legados (`proc`) para inclusão.
4.  **Build Backend**: Invoca o **PyInstaller** para empacotar o FastAPI, dependências e o Frontend estático em um único diretório.
5.  **Output**: Gera a pasta final `dist_v18/FinancialChecker` e um arquivo compactado `dist_v18/FinancialChecker_v1.8.zip`.

## 📂 Estrutura da Distribuição

O resultado final em `dist_v18/` terá:

*   **`FinancialChecker_v1.8.zip`**: Pacote pronto para envio ao cliente.
*   **`FinancialChecker/`**: Pasta descompactada (para testes locais).
    *   `FinancialChecker.exe`: O executável principal.
    *   `_internal/`: Dependências e assets.
    *   `web_dist/`: Arquivos estáticos do Next.js.
    *   `conf/`: Arquivos de configuração.
    *   `data/`: Banco de dados SQLite inicial.
    *   `proc/`: Regras de negócio legadas.

## 🧪 Validando a Distribuição

O script executa automaticamente um teste de 5 segundos após a build. Para validar manualmente:

1.  Navegue até `dist_v18/FinancialChecker`.
2.  Execute `FinancialChecker.exe`.
3.  O navegador padrão deve abrir automaticamente em `http://localhost:3000` (ou porta configurada).
4.  Verifique se o terminal/janela preta não apresenta erros de importação na inicialização.

---

**Nota Importante**: O diretório `dist_v18` não deve ser commitado no Git (está no `.gitignore`). Apenas o código fonte e scripts de build são versionados.

---

## 🗄️ Gerando o Banco Seed (MySQL → SQLite)

O banco `data/concilie.db` é copiado para `%APPDATA%\Financial\financial.db` na primeira execução do cliente. Ele deve conter apenas os **dados de referência** (tabelas de configuração), nunca dados de processamento de clientes.

### Pré-requisito

O `.env` ativo deve apontar para MySQL (`DATABASE_TYPE=mysql`):

```bash
# Verificar
cat apps/api/.env.active
```

### Gerar o seed

```bash
cd apps/api
python scripts/export_seed.py
```

O script:
1. Conecta ao MySQL configurado no `.env`
2. Cria o schema SQLite via modelos SQLAlchemy
3. Exporta as tabelas de referência: `bandeiras_cliente`, `bandeiras_disponiveis`, `taxas`, `contextos`, `termos_filtraveis`, `usuarios`
4. Salva em `data/concilie.db`
5. Exibe log de quantidades por tabela

> **Segurança**: O script recusa incluir tabelas de processamento (`vendas_processadas`, `recebiveis_processados`, `vendas_calculos`). Se passadas via `--tables`, o script aborta com erro.

### Saída esperada

```
INFO: === export_seed.py ===
INFO: Destino: E:\Financial_P\data\concilie.db
INFO: Tabelas: bandeiras_cliente, taxas, contextos, ...
INFO: Schema criado em: ...
INFO:   taxas: 42 registros exportados
INFO:   contextos: 3 registros exportados
INFO:   ...
INFO: ✅ Seed gerado com sucesso: 150 registros totais
INFO:    Arquivo: data/concilie.db (48.5 KB)
```

---

## 🔄 Alternando entre MySQL e SQLite localmente

O banco é controlado pela variável `DATABASE_TYPE` no `.env`:

```bash
# Usar MySQL (desenvolvimento)
echo "DATABASE_TYPE=mysql" > apps/api/.env.active
cp apps/api/.env.mysql apps/api/.env

# Usar SQLite (testar distribuição)
echo "DATABASE_TYPE=sqlite" > apps/api/.env.active
cp apps/api/.env.example apps/api/.env  # ajustar SQLITE_DB_PATH se necessário
```

Reiniciar o backend após trocar o `.env`.

---

## 🧪 Smoke Test SQLite

Antes de distribuir, verifique a compatibilidade SQLite rodando:

```bash
cd apps/api
pytest tests/test_sqlite_smoke.py -v
```

Todos os 17 testes devem passar. Qualquer falha indica regressão de compatibilidade.
