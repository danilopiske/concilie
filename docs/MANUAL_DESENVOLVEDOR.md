# Manual do Desenvolvedor - Concilie

Este documento é a referência técnica definitiva para manutenção e expansão do sistema **Financial Checker (Concilie)**.

---

## 1. Arquitetura do Sistema

O sistema segue uma arquitetura moderna híbrida, projetada para ser distribuída tanto como software local (Standalone) quanto como serviço web (SaaS).

### Diagrama de Stack
```mermaid
graph TD
    User[Usuário] -->|HTTP/3000| Frontend[Next.js 14]
    Frontend -->|REST/8000| Backend[FastAPI]
    Backend -->|SQLAlchemy| DB[(SQLite / MySQL)]
    Backend -->|Import| Legacy[Engine Legada (proc)]
    Legacy -->|Pandas| Sheets[Excel Reader]
```

### Componentes Chave

| Componente | Tecnologia | Versão | Função |
|------------|------------|--------|--------|
| **Frontend** | Node.js / React | 18+ / 18 | Interface do usuário (UI) e gestão de estado. |
| **Framework Web** | Next.js | 14.1 | Roteamento, SSR e Build estático (`export`). |
| **Backend** | Python | 3.11+ | Regras de negócio, API e orquestração. |
| **API Framework** | FastAPI | 0.111+ | Exposição de endpoints RESTful. |
| **ORM** | SQLAlchemy | 2.0+ | Abstração de banco de dados (Agnóstico). |
| **Engine** | Pandas | 2.2+ | Processamento massivo de arquivos Excel/CSV. |

---

## 2. Padrões de Desenvolvimento

### Backend (`apps/api`)
*   **Gerenciador de Pacotes**: `Poetry` (arquivo `pyproject.toml` na raiz).
*   **Estrutura**:
    *   `app/main.py`: Entrypoint da API.
    *   `app/api/v1/endpoints`: Controladores (Routes).
    *   `app/services`: Regras de negócio puras.
    *   `app/schemas`: Modelos Pydantic (DTOs).
    *   `app/models`: Modelos SQLAlchemy (Banco).
*   **Integração Legada**: O diretório `proc/` na raiz contém lógica complexa herdada do sistema Desktop. Ela deve ser importada com cuidado, adicionando a raiz ao `sys.path` se necessário.

### Frontend (`apps/web`)
*   **Gerenciador de Pacotes**: `pnpm` (Workspace).
*   **Estilização**: `Tailwind CSS`.
*   **Componentes**: `shadcn/ui` (em `components/ui`).
*   **API Client**: `lib/api/client.ts` (Axios configurado).

---

## 3. Ambiente de Desenvolvimento

### Setup Inicial
1.  **Python**: Instalar Python 3.11.
2.  **Node.js**: Instalar versão LTS (18 ou 20).
3.  **Ferramentas Globais**:
    ```bash
    pip install poetry
    npm install -g pnpm
    ```

### Rodando o Projeto
Para facilitar, use os scripts `.bat` na raiz:
*   `Iniciar Stack Moderno - SQLite.bat`: Sobe Backend (8000) e Frontend (3000).

### Banco de Dados
O sistema suporta **hibridismo**:
*   **Desenvolvimento**: Usa `data/concilie.db` (SQLite) por padrão.
*   **Produção**: Pode usar MySQL alterando a variável `DATABASE_URL` no `.env` ou `conf/db.env`.

---

## 4. Distribuição (Build)

O sistema possui um script de build customizado (`build_dist.py`) que:
1.  Compila o Next.js (`pnpm build`).
2.  Empacota o Python com PyInstaller.
3.  Inclui dependências manuais (`proc`, `conf`, `data`).

**Comando**:
```bash
python build_dist.py
```
**Resultado**: Gera uma pasta `dist_v18` pronta para zipar e enviar ao cliente.

---

## 5. Bibliotecas Principais

| Biblioteca | Versão | Uso |
|------------|--------|-----|
| `pandas` | ^2.3.0 | Leitura e transformação de dados Excel/CSV. |
| `sqlalchemy` | ^2.0.41 | Interação com banco de dados. |
| `pydantic` | ^2.7.0 | Validação de dados e Schemas. |
| `openpyxl` | ^3.1.5 | Engine de leitura Excel (.xlsx). |
| `axios` | ^1.6.0 | Requisições HTTP no frontend. |
| `lucide-react`| ^0.300 | Ícones do sistema. |

---

**Manutenedor**: Danilo Piske
**Última Atualização**: 22/01/2026
