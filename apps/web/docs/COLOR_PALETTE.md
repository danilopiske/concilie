# Paleta de Cores - Financial Checker

## Visão Geral
Sistema de cores corporativo com **fundo claro**, otimizado para clareza e confiança em contexto financeiro.

---

## Cores Principais

### 🔵 Azul (Primary) - Confiança e Ações
- **Uso**: Botões primários, links, estados de foco, elementos interativos
- **Shades**:
  - 50: `#EFF6FF` (hover suave)
  - 100: `#DBEAFE` (badges info)
  - 500: `#3B82F6` (botão primary)
  - 600: `#2563EB` (hover primary)
  - 700: `#1D4ED8` (active state)
  - 900: `#1E3A8A` (texto enfático)

**Exemplos de Uso:**
```tsx
<Button variant="primary">Salvar</Button>
<a className="text-blue-600 hover:text-blue-700">Editar</a>
<input className="focus:ring-blue-500" />
```

---

### 🟡 Dourado/Amber (Premium)
- **Uso**: Destaques especiais, clientes VIP, recursos premium, taxas especiais
- **Shades**:
  - 100: `#FEF3C7` (badge background)
  - 500: `#F59E0B` (ícones dourados)
  - 600: `#D97706` (hover)

**Exemplos de Uso:**
```tsx
<Badge variant="gold">Cliente Premium</Badge>
<Button variant="gold">Upgrade para Premium</Button>
<div className="bg-amber-100 border-amber-300">Oferta Especial</div>
```

---

### 🔴 Vermelho (Danger) - Erros e Alertas
- **Uso**: Erros, ações destrutivas, alertas críticos
- **Shades**:
  - 50: `#FEF2F2` (alert background)
  - 100: `#FEE2E2` (badge error)
  - 500: `#EF4444` (botão danger)
  - 600: `#DC2626` (hover danger)
  - 900: `#7F1D1D` (texto erro)

**Exemplos de Uso:**
```tsx
<Button variant="danger">Excluir</Button>
<Alert variant="error">Erro ao processar</Alert>
<Badge variant="error">Inativo</Badge>
```

---

### 🟢 Verde (Success) - Confirmações
- **Uso**: Sucesso, confirmações, status ativo
- **Shades**:
  - 50: `#F0FDF4` (alert success)
  - 100: `#DCFCE7` (badge success)
  - 500: `#22C55E` (botão success)
  - 600: `#16A34A` (hover)
  - 800: `#166534` (texto sucesso)

**Exemplos de Uso:**
```tsx
<Button variant="success">Confirmar</Button>
<Alert variant="success">Operação concluída</Alert>
<Badge variant="success">Ativo</Badge>
```

---

## Cores Neutras

### ⚪ Cinza (Neutral) - Backgrounds e Textos
- **50**: `#F9FAFB` - Backgrounds de tabela
- **100**: `#F3F4F6` - Hover em elementos neutros
- **200**: `#E5E7EB` - Bordas
- **300**: `#D1D5DB` - Bordas mais escuras
- **500**: `#6B7280` - Texto secundário
- **700**: `#374151` - Texto principal
- **900**: `#111827` - Títulos

**Exemplos de Uso:**
```tsx
<thead className="bg-gray-50">
<button className="bg-gray-100 hover:bg-gray-200 text-gray-700">
<p className="text-gray-500">Texto secundário</p>
```

---

## Fundos

### Página Principal
- **Background primário**: `#FFFFFF` (branco puro)
- **Background secundário**: `#F9FAFB` (cinza 50 - cards, tabelas)
- **Background terciário**: `#F3F4F6` (cinza 100 - headers de tabela)

### Cards
- **Default**: `bg-white` com `border-gray-200`
- **Success**: `bg-green-50` com `border-green-300`
- **Warning**: `bg-yellow-50` com `border-amber-400`
- **Error**: `bg-red-50` com `border-red-300`

---

## Texto

### Hierarquia
- **Primário**: `text-gray-900` (#111827) - Títulos, labels principais
- **Secundário**: `text-gray-700` (#374151) - Textos normais
- **Terciário**: `text-gray-500` (#6B7280) - Placeholders, textos auxiliares
- **Inverso**: `text-white` - Texto sobre backgrounds escuros (botões primary/danger)

---

## Bordas

- **Light**: `border-gray-200` - Bordas padrão de cards/inputs
- **Medium**: `border-gray-300` - Bordas de botões secondary
- **Dark**: `border-gray-400` - Bordas em estados hover

---

## Sombras

### Elevação
- **sm**: `0 1px 2px 0 rgba(0, 0, 0, 0.05)` - Cards, badges
- **md**: `0 4px 6px -1px rgba(0, 0, 0, 0.1)` - Modais, dropdowns
- **lg**: `0 10px 15px -3px rgba(0, 0, 0, 0.1)` - Elementos flutuantes
- **xl**: `0 20px 25px -5px rgba(0, 0, 0, 0.1)` - Overlays

**Uso nos Componentes:**
```tsx
// Botões primários
className="shadow-sm hover:shadow-md"

// Botão gold (mais destaque)
className="shadow-md hover:shadow-lg"

// Cards
className="shadow-sm"

// Tabelas
className="shadow-sm"
```

---

## Componentes por Cor

### Azul (Primary)
- **Button** variant="primary"
- **Badge** variant="info"
- **Alert** variant="info"
- **Links** ativos
- **Focus rings**
- **Indicadores de sort** em tabelas

### Dourado (Gold)
- **Button** variant="gold"
- **Badge** variant="gold"
- Destaques premium
- Clientes VIP

### Vermelho (Danger)
- **Button** variant="danger"
- **Badge** variant="error"
- **Alert** variant="error"
- Mensagens de erro
- Ações destrutivas

### Verde (Success)
- **Button** variant="success"
- **Badge** variant="success"
- **Alert** variant="success"
- Confirmações

### Cinza (Neutral)
- **Button** variant="secondary"
- **Badge** variant="default"
- Backgrounds de tabela
- Bordas

---

## Diretrizes de Uso

### ✅ Boas Práticas
- Usar **azul** para ações principais (apenas 1 por tela)
- Usar **dourado** com moderação (apenas para destaque real)
- **Vermelho** apenas para erros/exclusões (nunca para ações neutras)
- **Verde** para feedbacks positivos
- Manter **contraste mínimo 4.5:1** para acessibilidade
- Usar `shadow-sm` como padrão, `shadow-lg` apenas em modais

### ❌ Evitar
- Múltiplos botões primary (azul) na mesma tela
- Dourado em elementos comuns (banaliza o destaque)
- Vermelho para ações não-destrutivas
- Fundos escuros (dificulta leitura de dados financeiros)
- Cores vibrantes em grandes áreas (cansa visão)

---

## Acessibilidade

### Contraste de Texto
| Fundo | Texto | Contraste | Status |
|-------|-------|-----------|--------|
| `bg-white` | `text-gray-900` | 16:1 | ✅ AAA |
| `bg-blue-600` | `text-white` | 4.8:1 | ✅ AA |
| `bg-red-600` | `text-white` | 4.7:1 | ✅ AA |
| `bg-gray-100` | `text-gray-700` | 7.2:1 | ✅ AAA |
| `bg-yellow-100` | `text-amber-900` | 8.5:1 | ✅ AAA |

### Estados Interativos
- **Focus**: Sempre com `focus:ring-2 focus:ring-{color}-500 focus:ring-offset-2`
- **Hover**: Mudança de cor + sombra (`hover:shadow-md`)
- **Active**: Cor mais escura (`active:bg-blue-800`)
- **Disabled**: Opacidade 50% + cursor not-allowed

---

## Migração do Dark Mode

### Antes (Dark Mode)
```tsx
className="bg-gray-800 dark:bg-gray-900 text-white dark:text-gray-100"
```

### Depois (Light Theme)
```tsx
className="bg-white text-gray-900"
```

### Componentes Atualizados
- ✅ **Button**: Cores mais vibrantes, shadow-sm, gold variant
- ✅ **Badge**: Bordas adicionadas, variant gold
- ✅ **Alert**: Bordas mais escuras, backgrounds suaves
- ✅ **Table**: Header bg-gray-50, hover bg-blue-50
- ✅ **Card**: Shadow-md, border-gray-200, header bg-gray-50
- ✅ **Checkbox**: Removido dark mode

---

## Tokens Semânticos

### Usando design-tokens.ts
```typescript
import { colors, shadows, spacing } from '@/lib/design-tokens';

// Ao invés de:
className="bg-blue-600"

// Use (quando precisar de estilos inline):
style={{ backgroundColor: colors.primary[600] }}

// Ou prefira Tailwind (já alinhado com tokens):
className="bg-blue-600"  // OK - Tailwind segue mesma paleta
```

---

## Exemplos Completos

### Botão Primário
```tsx
<Button 
  variant="primary"     // bg-blue-600, shadow-sm
  loading={isSaving}    // Spinner azul
>
  Salvar Alterações
</Button>
```

### Alerta de Sucesso
```tsx
<Alert variant="success">  {/* bg-green-50, border-green-300 */}
  Processamento concluído com sucesso! 150 registros importados.
</Alert>
```

### Badge Premium
```tsx
<Badge variant="gold">  {/* bg-gradient from-yellow-100 */}
  Cliente VIP
</Badge>
```

### Tabela com Hover
```tsx
<Table 
  columns={columns}
  data={vendas}
  // Header: bg-gray-50
  // Row hover: bg-blue-50
  // Sort indicator: text-blue-600
/>
```

---

## Changelog

### v2.0 (Janeiro 2026)
- ✅ Migração completa de dark mode para light theme
- ✅ Adição de variant "gold" em Button e Badge
- ✅ Padronização de shadows (sm → md → lg)
- ✅ Bordas adicionadas em badges e alerts
- ✅ Table hover alterado de gray para blue-50
- ✅ Card header com bg-gray-50
- ✅ Todos componentes sem classes dark:*

---

**Nota**: Esta paleta foi escolhida para refletir profissionalismo, confiança e clareza - valores essenciais em sistemas financeiros.
