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
5.  **Output**: Gera a pasta final `dist_v18/FinancialChecker`.

## 📂 Estrutura da Distribuição

O resultado final em `dist_v18/FinancialChecker` terá a seguinte estrutura:

*   `FinancialChecker.exe`: O executável principal que inicia Backend e serve o Frontend.
*   `_internal/`: Pasta contendo dependências Python congeladas e assets.
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
