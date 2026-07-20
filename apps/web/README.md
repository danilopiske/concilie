# Concilie Web — Frontend Next.js

Interface web do sistema Concilie de reconciliação financeira, construída com Next.js 15 + Tailwind CSS.

## Pré-requisitos

- Node.js 20+
- [pnpm](https://pnpm.io/) 10+

## Setup

```bash
# Na raiz do monorepo
cd apps/web

# Instalar dependências
pnpm install

# Copiar e preencher variáveis de ambiente
cp .env.example .env.local
# Edite .env.local com as configurações locais
```

## Variáveis de Ambiente

Veja `.env.example` para a lista completa.

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `NEXT_PUBLIC_API_URL` | URL do backend FastAPI | `http://localhost:8000` |

## Executar

```bash
# Modo desenvolvimento
pnpm dev
# Acesse: http://localhost:3000

# Build de produção
pnpm build
pnpm start
```

## Testes

```bash
# E2E com Playwright (requer API + Next.js rodando)
pnpm test:e2e

# Com UI do Playwright
pnpm test:e2e:headed

# Ver relatório HTML dos testes
pnpm test:e2e:report
```

## Lint e Typecheck

```bash
# ESLint
pnpm lint

# TypeScript
pnpm typecheck
```

## Estrutura

```
src/
├── app/            # App Router (Next.js 15)
├── components/     # Componentes React reutilizáveis
├── lib/            # Utilitários e clientes API
└── types/          # Definições TypeScript
e2e/                # Testes E2E Playwright
├── helpers/        # Utilitários de teste (auth, etc.)
└── *.spec.ts       # Test specs por funcionalidade
```
