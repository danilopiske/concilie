# 🚀 Context7 MCP - Guia Rápido

## O que é Context7?

Context7 é um servidor MCP que fornece **documentação atualizada** de bibliotecas e frameworks diretamente para sua IA. Nunca mais código desatualizado ou APIs inexistentes!

## ✅ Já Configurado

O Context7 já está ativo no seu VSCode via arquivo `.vscode/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "context7": {
        "url": "https://mcp.context7.com/mcp"
      }
    }
  }
}
```

## 🎯 Como Usar

### Método 1: Automático (Recomendado)

A regra em `.cursorrules` já ativa o Context7 automaticamente para perguntas sobre código.

**Exemplos:**
- "Como criar um endpoint FastAPI?"
- "Setup Next.js com TypeScript"
- "Configurar SQLAlchemy com MySQL"

### Método 2: Explícito

Adicione `use context7` no final do prompt:

```
Crie um middleware Next.js para validar JWT. use context7
```

### Método 3: Com Library ID

Se você sabe a biblioteca exata, use o ID:

```
Configure Supabase auth. use library /supabase/supabase for API and docs.
```

## 📚 Bibliotecas Principais do Projeto

### Backend (Python)
- **FastAPI**: `/tiangolo/fastapi`
- **SQLAlchemy**: `/sqlalchemy/sqlalchemy`
- **Pydantic**: `/pydantic/pydantic`
- **Panel**: `/holoviz/panel`

### Frontend (TypeScript)
- **Next.js**: `/vercel/next.js`
- **React**: `/facebook/react`
- **TypeScript**: `/microsoft/TypeScript`

### DevOps
- **Poetry**: `/python-poetry/poetry`
- **pnpm**: `/pnpm/pnpm`

## 💡 Recursos Context7

### 🔧 Ferramentas Disponíveis

1. **resolve-library-id**: Encontra o ID correto da biblioteca
   ```
   Parâmetros:
   - query: sua pergunta
   - libraryName: nome da biblioteca
   ```

2. **query-docs**: Busca documentação específica
   ```
   Parâmetros:
   - libraryId: ID da biblioteca (ex: /vercel/next.js)
   - query: sua pergunta
   ```

### 🎓 Dicas de Uso

#### 1. Especifique Versão
```
Como usar middleware no Next.js 14? use context7
```

#### 2. Seja Específico
```
❌ "Como usar FastAPI?"
✅ "Como criar endpoint POST com validação Pydantic no FastAPI? use context7"
```

#### 3. Contexto do Projeto
```
Preciso migrar Panel para Next.js, mantendo a lógica de autenticação atual. use context7
```

## 🚀 Casos de Uso para Financial Checker

### 1. Migração Frontend
```
Como estruturar um projeto Next.js 14 com App Router para migração de Panel? use context7
```

### 2. Backend Moderno
```
Como organizar um projeto FastAPI com Repository Pattern e Dependency Injection? use context7
```

### 3. Dual Database
```
Como fazer SQLAlchemy funcionar com MySQL e SQLite usando o mesmo código? use context7
```

### 4. Autenticação
```
Implementar JWT authentication no FastAPI com refresh tokens. use context7
```

### 5. TypeScript Types
```
Como definir tipos TypeScript para responses da API FastAPI? use context7
```

## 📊 Benefícios

### ✅ Antes do Context7
- ❌ Código desatualizado
- ❌ APIs que não existem mais
- ❌ Exemplos genéricos
- ❌ Resposta baseada em dados antigos

### ✨ Depois do Context7
- ✅ Documentação atual
- ✅ APIs verificadas
- ✅ Exemplos práticos
- ✅ Código que funciona de primeira

## 🔑 API Key (Opcional)

Para limites maiores, crie uma chave gratuita:

1. Acesse: https://context7.com/dashboard
2. Crie uma conta
3. Copie sua API key
4. Adicione no `.vscode/settings.json`:

```json
{
  "mcp": {
    "servers": {
      "context7": {
        "url": "https://mcp.context7.com/mcp",
        "headers": {
          "Authorization": "Bearer SUA_API_KEY"
        }
      }
    }
  }
}
```

## 🐛 Troubleshooting

### Context7 não responde

1. **Verifique conexão internet**
   ```bash
   ping mcp.context7.com
   ```

2. **Recarregue VSCode**
   ```
   Ctrl+Shift+P → Reload Window
   ```

3. **Verifique configuração**
   - Arquivo: `.vscode/settings.json`
   - Seção: `"mcp"`

### Respostas genéricas

Use `use context7` explicitamente no prompt:
```
Sua pergunta aqui. use context7
```

## 📖 Mais Informações

- Site: https://context7.com
- Docs: https://context7.com/docs
- GitHub: https://github.com/upstash/context7
- Discord: https://upstash.com/discord

---

**Última atualização**: 08/01/2026  
**Versão Context7**: Latest  
**Projeto**: Financial Checker v2.0
