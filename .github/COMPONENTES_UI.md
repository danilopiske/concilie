# Componentes UI - Design System

**Data de Criação:** 11/01/2026  
**Status:** ✅ Componentes Base Criados

---

## 📦 Componentes Disponíveis

### 1. **Table** (`Table.tsx`)

Tabela reutilizável com formatação automática e ordenação.

**Props:**
```typescript
interface TableProps<T> {
  variant?: 'simple' | 'info';
  columns: TableColumn<T>[];
  data: T[];
  onSort?: (key: string) => void;
  emptyMessage?: string;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
}

interface TableColumn<T> {
  key: string;
  label: string;
  sortable?: boolean;
  format?: 'currency' | 'date' | 'boolean' | 'badge';
  render?: (value: any, row: T) => ReactNode;
  width?: string;
}
```

**Uso:**
```tsx
<Table
  variant="simple"
  columns={[
    { key: 'id', label: 'ID', width: '80px' },
    { key: 'nome', label: 'Nome', sortable: true },
    { key: 'valor', label: 'Valor', format: 'currency' },
    { key: 'ativo', label: 'Status', render: (value) => <Badge variant={value ? 'success' : 'error'}>{value ? 'Ativo' : 'Inativo'}</Badge> }
  ]}
  data={items}
  onSort={handleSort}
  sortKey={sortKey}
  sortDirection={sortDirection}
/>
```

**Features:**
- ✅ Formatação automática (currency, date, boolean)
- ✅ Custom render por coluna
- ✅ Ordenação com indicador visual
- ✅ Empty state configurável
- ✅ Hover em linhas
- ✅ Dark mode

---

### 2. **Badge** (`Badge.tsx`)

Badge para status e categorias.

**Props:**
```typescript
interface BadgeProps {
  variant?: 'success' | 'error' | 'warning' | 'info' | 'default';
  children: ReactNode;
  className?: string;
}
```

**Uso:**
```tsx
<Badge variant="success">Ativo</Badge>
<Badge variant="error">Inativo</Badge>
<Badge variant="warning">Pendente</Badge>
<Badge variant="info">Em análise</Badge>
<Badge>Padrão</Badge>
```

**Variantes:**
- `success`: Verde (confirmação, ativo)
- `error`: Vermelho (erro, inativo)
- `warning`: Amarelo (atenção, pendente)
- `info`: Azul (informação)
- `default`: Cinza (neutro)

---

### 3. **Checkbox** (`Checkbox.tsx`)

Checkbox com label associado e acessibilidade.

**Props:**
```typescript
interface CheckboxProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
  error?: string;
}
```

**Uso:**
```tsx
<Checkbox
  label="Incluir inativos"
  checked={incluirInativos}
  onChange={setIncluirInativos}
  disabled={loading}
  error={errors.termos}
/>
```

**Features:**
- ✅ Label associado com `htmlFor`
- ✅ Estados: default, disabled, error
- ✅ Focus visível
- ✅ ARIA attributes
- ✅ Dark mode

---

### 4. **ConfirmDialog** (`ConfirmDialog.tsx`)

Modal de confirmação reutilizável.

**Props:**
```typescript
interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'danger' | 'warning' | 'info';
  loading?: boolean;
}
```

**Uso:**
```tsx
<ConfirmDialog
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={handleDelete}
  title="Confirmar Exclusão"
  message={`Deseja realmente excluir "${item.nome}"?`}
  confirmText="Excluir"
  cancelText="Cancelar"
  variant="danger"
  loading={deleting}
/>
```

**Variantes:**
- `danger`: Ação destrutiva (excluir, remover)
- `warning`: Ação importante (alterar, processar)
- `info`: Confirmação neutra (salvar, continuar)

**Features:**
- ✅ Suporte a async/await
- ✅ Loading state automático
- ✅ Ícone por variante
- ✅ Bloqueia ações durante loading
- ✅ Fecha automaticamente após confirmação

---

### 5. **Alert** (`Alert.tsx`)

Mensagens de feedback para o usuário.

**Props:**
```typescript
interface AlertProps {
  variant?: 'info' | 'success' | 'error' | 'warning';
  children: ReactNode;
  onClose?: () => void;
  className?: string;
}
```

**Uso:**
```tsx
<Alert variant="success">
  Cliente salvo com sucesso!
</Alert>

<Alert variant="error" onClose={() => setError(null)}>
  Erro ao processar: verifique os campos obrigatórios.
</Alert>

<Alert variant="info">
  Preencha todos os campos antes de continuar.
</Alert>
```

**Variantes:**
- `info`: Informação neutra (azul)
- `success`: Sucesso/confirmação (verde)
- `error`: Erro/falha (vermelho)
- `warning`: Atenção/aviso (amarelo)

**Features:**
- ✅ Ícone por variante
- ✅ Botão de fechar opcional
- ✅ ARIA role="alert"
- ✅ Dark mode
- ✅ Border esquerda colorida

---

### 6. **Button** (Atualizado)

Botão com loading state e variante text.

**Novas Props:**
```typescript
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'text';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;  // NOVO
  // ...
}
```

**Novidades:**
```tsx
// Loading state
<Button variant="primary" loading={isSaving}>
  Salvar
</Button>

// Variante text (para ações secundárias)
<Button variant="text" onClick={handleEdit}>
  Editar
</Button>
```

**Features Adicionadas:**
- ✅ Loading spinner integrado
- ✅ Desabilita automaticamente quando loading
- ✅ Variante `text` para botões de ação inline
- ✅ Gap para ícones

---

## 🎯 Como Usar nos Módulos

### **Antes (❌ Errado):**

```tsx
// Loading manual
if (loading) {
  return <div className="p-6"><p>Carregando...</p></div>;
}

// Erro manual
if (error) {
  return <div className="p-6"><p className="text-red-500">Erro: {error}</p></div>;
}

// Tabela HTML
<table className="min-w-full">
  <thead>...</thead>
  <tbody>...</tbody>
</table>

// Badge manual
<span className={`px-2 py-1 ${ativo ? 'bg-green-100' : 'bg-red-100'}`}>
  {ativo ? 'Ativo' : 'Inativo'}
</span>

// Confirm nativo
if (!confirm('Deseja excluir?')) return;

// Checkbox HTML
<input type="checkbox" checked={checked} onChange={...} />
```

### **Depois (✅ Correto):**

```tsx
import { Table, Badge, Alert, ConfirmDialog, Checkbox } from '@/components/ui';
import { Loading } from '@/components/shared/Loading';

// Loading component
if (loading) return <Loading />;

// Alert component
if (error) return <Alert variant="error">{error}</Alert>;

// Table component
<Table
  columns={COLUMNS}
  data={items}
  onSort={handleSort}
/>

// Badge component
<Badge variant={ativo ? 'success' : 'error'}>
  {ativo ? 'Ativo' : 'Inativo'}
</Badge>

// ConfirmDialog component
<ConfirmDialog
  isOpen={showConfirm}
  onConfirm={handleDelete}
  title="Confirmar Exclusão"
  message="Deseja excluir?"
  variant="danger"
/>

// Checkbox component
<Checkbox
  label="Incluir inativos"
  checked={checked}
  onChange={setChecked}
/>
```

---

## 📋 Checklist de Migração

Para migrar uma página existente:

- [ ] Substituir tabelas HTML por `<Table>`
- [ ] Substituir badges manuais por `<Badge>`
- [ ] Substituir loading/error manual por `<Loading>` e `<Alert>`
- [ ] Substituir `alert()` e `confirm()` por `<ConfirmDialog>`
- [ ] Substituir checkbox HTML por `<Checkbox>`
- [ ] Substituir botões HTML por `<Button variant="text">`
- [ ] Remover classes Tailwind hardcoded
- [ ] Validar apenas 1 botão primary por tela
- [ ] Testar acessibilidade (tab, enter, esc)
- [ ] Testar dark mode

---

## 🚀 Próximos Passos

1. **Refatorar Contextos** (projeto piloto)
2. **Refatorar Bandeiras**
3. **Refatorar Clientes**
4. **Criar guia de padrões visuais** (cores, espaçamento, etc.)
5. **Documentar tokens semânticos**

---

**Status:** ✅ Componentes prontos para uso  
**Próxima Ação:** Refatorar página de Contextos como piloto
