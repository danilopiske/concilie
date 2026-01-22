# Concilie - Financial Checker

**Concilie** é uma plataforma avançada de conciliação financeira e gestão de transações, projetada para processar, validar e analisar grandes volumes de dados de vendas (cartões, PIX, etc.) e recebíveis. O sistema oferece uma interface web moderna para importação de arquivos, criação de regras de negócio (De-Para), dashboards de análise e relatórios detalhados.

---

## 🚀 Visão Geral da Tecnologia

O sistema utiliza uma arquitetura híbrida moderna, garantindo alta performance e facilidade de distribuição:

*   **Frontend**: [Next.js](https://nextjs.org/) (React) com Tailwind CSS para uma interface responsiva e intuitiva.
*   **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python) para uma API robusta, assíncrona e tipada.
*   **Core de Processamento**: Engine Python legado (`proc`) para leitura de arquivos complexos (Excel/CSV) e regras de negócio consolidadas.
*   **Banco de Dados**: Suporte híbrido para **SQLite** (distribuição standalone) e **MySQL** (ambientes robustos).

## 📂 Estrutura do Projeto

*   `apps/web`: Código fonte do Frontend (Next.js).
*   `apps/api`: Código fonte da API (FastAPI).
*   `proc`: Lógica de processamento e regras de negócio (Legado/Core).
*   `conf`: Arquivos de configuração e conexão com banco de dados.
*   `data`: Diretório para armazenamento de banco de dados local (SQLite).
*   `docs`: Documentação técnica e manuais.

## 📚 Documentação

Para detalhes específicos, consulte os manuais abaixo na pasta `docs/`:

1.  **[Descritivo do Sistema](docs/DESCRITIVO_SISTEMA.md)**: Detalhamento funcional de todos os módulos (Conciliação, Importação, Cadastros).
2.  **[Guia de Instalação](docs/GUIA_INSTALACAO.md)**: Passo-a-passo para instalação em ambientes de produção/clientes.
3.  **[Guia de Distribuição](docs/GUIA_DISTRIBUICAO.md)**: Instruções para desenvolvedores gerarem o executável (`.exe`) do sistema.

## 🛠️ Início Rápido (Desenvolvimento)

Pré-requisitos: Python 3.11+, Node.js 18+, pnpm.

1.  **Instalar Dependências**:
    ```bash
    # Backend
    cd apps/api
    poetry install

    # Frontend
    cd apps/web
    pnpm install
    ```

2.  **Rodar o Sistema Localmente**:
    Use o script `Iniciar Stack Moderno - SQLite.bat` na raiz do projeto, ou inicie manualmente:
    *   Backend: `poetry run uvicorn app.main:app --reload`
    *   Frontend: `pnpm dev`

---

**Desenvolvido por Danilo Piske**
*Versão 1.8 - Next.js Migration*
