# Análise UI Design System - Módulos Migrados

**Data:** 11/01/2026  
**Módulos Analisados:** Clientes, Contextos, Bandeiras

---

## ❌ VIOLAÇÕES CRÍTICAS ENCONTRADAS

### 1. **ESTILOS INLINE E HARDCODED**

**Problema:** Uso de `className` com cores diretas (Tailwind) em vez de tokens semânticos

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 70
<h1 className="text-2xl font-bold text-gray-900 dark:text-white">

// ❌ ERRADO - bandeiras/page.tsx linha 106
className="text-red-600 hover:text-red-900"

// ❌ ERRADO - contextos/page.tsx linha 130
className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
  contexto.ativo
    ? 'bg-green-100 text-green-800'
    : 'bg-red-100 text-red-800'
}`}
```

**Impacto:** Viola regra "NÃO usar cores diretas - usar tokens semânticos"

---

### 2. **TABELAS NÃO COMPONENTIZADAS**

**Problema:** Tabelas escritas manualmente com HTML/Tailwind, não usando componente `<Table>`

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linhas 88-160
<table className="min-w-full divide-y divide-gray-200">
  <thead>...</thead>
  <tbody>...</tbody>
</table>

// ❌ ERRADO - bandeiras/page.tsx linhas 66-120
<table className="min-w-full">...</table>
```

**Deveria ser:**
```tsx
// ✅ CORRETO
<Table
  variant="simple"
  columns={COLUMNS}
  data={contextos}
/>
```

---

### 3. **LOADING E ERROR SEM COMPONENTES**

**Problema:** Estados de loading/error renderizados como HTML direto

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 50
if (loading) {
  return (
    <div className="p-6">
      <p>Carregando...</p>
    </div>
  );
}

// ❌ ERRADO - contextos/page.tsx linha 57
if (error) {
  return (
    <div className="p-6">
      <p className="text-red-500">Erro: {error}</p>
    </div>
  );
}
```

**Deveria ser:**
```tsx
// ✅ CORRETO
if (loading) return <Loading />;
if (error) return <Alert variant="error">{error}</Alert>;
```

---

### 4. **BOTÕES NÃO PADRONIZADOS**

**Problema:** Botões de ação (editar, excluir) escritos como `<button>` HTML

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 143
<button
  onClick={() => handleEditContexto(contexto)}
  className="text-blue-600 hover:text-blue-900"
>
  Editar
</button>
```

**Deveria ser:**
```tsx
// ✅ CORRETO
<Button variant="text" size="small" onClick={() => handleEdit(contexto)}>
  Editar
</Button>
```

---

### 5. **BADGES/STATUS SEM COMPONENTE**

**Problema:** Badges de status criadas manualmente

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 129
<span
  className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
    contexto.ativo
      ? 'bg-green-100 text-green-800'
      : 'bg-red-100 text-red-800'
  }`}
>
  {contexto.ativo ? 'Ativo' : 'Inativo'}
</span>
```

**Deveria ser:**
```tsx
// ✅ CORRETO
<Badge variant={contexto.ativo ? 'success' : 'error'}>
  {contexto.ativo ? 'Ativo' : 'Inativo'}
</Badge>
```

---

### 6. **MÚLTIPLOS BOTÕES PRIMARY**

**Problema:** Potencial violação da regra "apenas 1 botão primary por tela"

**Verificação Necessária:** Conferir se modais/formulários têm mais de 1 botão primary

---

### 7. **FALTA DE CARD PARA AGRUPAMENTO**

**Problema:** Conteúdo não está dentro de `<Card>` para separação visual

**Exemplos:**
```tsx
// ❌ ERRADO - bandeiras/page.tsx linha 66
<div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
  <table>...</table>
</div>
```

**Deveria ser:**
```tsx
// ✅ CORRETO
<Card>
  <Table data={bandeiras} columns={COLUMNS} />
</Card>
```

---

### 8. **ALERT NATIVO EM VEZ DE COMPONENTE**

**Problema:** Uso de `alert()` JavaScript nativo

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 39
alert(err.response?.data?.detail || 'Erro ao excluir contexto');
```

**Deveria ser:**
```tsx
// ✅ CORRETO
setError(err.response?.data?.detail || 'Erro ao excluir contexto');
// E renderizar: <Alert variant="error">{error}</Alert>
```

---

### 9. **CONFIRM NATIVO EM VEZ DE MODAL**

**Problema:** Uso de `confirm()` JavaScript nativo

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 33
if (!confirm(`Deseja realmente excluir...`)) {
  return;
}
```

**Deveria ser:**
```tsx
// ✅ CORRETO
<ConfirmDialog
  title="Confirmar Exclusão"
  message={`Deseja realmente excluir "${contexto.nome}"?`}
  onConfirm={handleDelete}
/>
```

---

### 10. **CHECKBOX SEM COMPONENTE**

**Problema:** Checkbox HTML nativo em vez de componente

**Exemplos:**
```tsx
// ❌ ERRADO - contextos/page.tsx linha 75
<input
  type="checkbox"
  checked={incluirInativos}
  onChange={(e) => setIncluirInativos(e.target.checked)}
  className="mr-2 h-4 w-4 text-blue-600 rounded"
/>
```

**Deveria ser:**
```tsx
// ✅ CORRETO
<Checkbox
  label="Incluir inativos"
  checked={incluirInativos}
  onChange={setIncluirInativos}
/>
```

---

## 📊 RESUMO DE CONFORMIDADE

| Módulo | Componentes | Tokens | Loading/Error | Tabelas | Botões | Score |
|--------|-------------|--------|---------------|---------|--------|-------|
| Clientes | ⚠️ Parcial | ❌ Não | ✅ Sim | ❌ HTML | ⚠️ Misto | 40% |
| Contextos | ❌ Não | ❌ Não | ❌ Não | ❌ HTML | ❌ HTML | 10% |
| Bandeiras | ❌ Não | ❌ Não | ❌ Não | ❌ HTML | ❌ HTML | 10% |

---

## 🎯 AÇÕES CORRETIVAS NECESSÁRIAS

### Prioridade CRÍTICA:
1. ✅ Criar componente `<Table>` reutilizável
2. ✅ Criar componente `<Badge>` para status
3. ✅ Criar componente `<Checkbox>` 
4. ✅ Criar componente `<ConfirmDialog>`
5. ✅ Substituir todas tabelas HTML por `<Table>`
6. ✅ Substituir todos loading/error por componentes

### Prioridade ALTA:
7. ✅ Criar tokens de cor semânticos
8. ✅ Substituir classes Tailwind diretas por tokens
9. ✅ Substituir botões HTML por `<Button>`
10. ✅ Substituir `alert()` e `confirm()` por componentes

### Prioridade MÉDIA:
11. ✅ Adicionar `<Card>` para agrupamento
12. ✅ Validar apenas 1 botão primary por tela
13. ✅ Revisar acessibilidade (aria-labels)

---

## 📝 COMPONENTES FALTANTES A CRIAR

1. **Table** (Prioridade 1)
   - Props: variant, columns, data, onSort, pagination
   - Variantes: simple, info
   - Formatação: currency, date, boolean

2. **Badge** (Prioridade 1)
   - Props: variant, children
   - Variantes: success, error, warning, info, default

3. **Checkbox** (Prioridade 2)
   - Props: label, checked, onChange, disabled
   - Com label associado e aria

4. **ConfirmDialog** (Prioridade 2)
   - Props: title, message, onConfirm, onCancel
   - Modal de confirmação reutilizável

5. **Alert** (Prioridade 1)
   - Se não existir, criar com variants: info, success, error, warning

6. **Loading** (Prioridade 1)
   - Se não existir, criar spinner padrão

---

## 🔄 PRÓXIMOS PASSOS

1. **Fase 1:** Criar componentes base faltantes (Table, Badge, Checkbox, ConfirmDialog)
2. **Fase 2:** Refatorar Contextos page (projeto piloto)
3. **Fase 3:** Refatorar Bandeiras page
4. **Fase 4:** Refatorar Clientes page
5. **Fase 5:** Criar guia de migração para próximos módulos

---

**Conclusão:** Os módulos migrados estão em **não conformidade** com o UI Design System estabelecido. Necessário refatoração completa seguindo os padrões documentados.
