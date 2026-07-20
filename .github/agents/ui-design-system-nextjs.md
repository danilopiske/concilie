# UI DESIGN SYSTEM – NEXT.JS (AGENT READY)

> Fonte única de verdade para geração de interfaces em Next.js  
> Este documento deve ser seguido por qualquer agent, LLM ou desenvolvedor

---

## 0. CONTEXTO TÉCNICO

Framework: Next.js (App Router)  
Linguagem: TypeScript  
Paradigma: Componentes reutilizáveis  
Domínio: Sistemas corporativos / fiscais / SPED

---

## 1. REGRAS GLOBAIS (OBRIGATÓRIAS)

- NÃO criar estilos inline  
- NÃO criar novos padrões visuais sem registro  
- SEMPRE reutilizar componentes existentes  
- SEMPRE prever estados (loading, error, disabled)  
- CLAREZA > estética  

---

## 2. TOKENS DE DESIGN (SEMÂNTICOS)

- color.primary → ações principais  
- color.secondary → ações alternativas  
- color.success → sucesso  
- color.error → erro  
- color.info → informação  
- color.disabled → desabilitado  

Espaçamento: xs | sm | md | lg | xl  
Radius: sm | md  
Fontes: body | label | title  

---

## 3. COMPONENTES

### Button
Variantes: primary, secondary, success, text, icon, small  
Estados: default, hover, disabled, loading  

Regras:
- Apenas 1 botão primary por tela
- loading desabilita clique

---

### InputText
Variantes: text, email, password, cnpj_raiz, textarea  
Estados: default, focus, disabled, error  

Regras:
- Label obrigatório
- Placeholder instrutivo

---

### FileUpload
Estados: empty, selected, loading, error  

Regras:
- Mostrar tipos aceitos
- Mostrar nome do arquivo
- Nunca processar automaticamente

---

### Stepper
Uso: fluxos longos e processamento fiscal  

---

### Card
Variantes: default, success, disabled  

---

### Alert
Variantes: info, success, error  

Regra:
- Mensagem de erro deve orientar ação corretiva

---

### Table
Variantes: simple, info  

---

## 4. LAYOUT PADRÃO DO SISTEMA

### 4.1. Estrutura Global

O sistema utiliza um layout fixo composto por:
- **TopBar (Barra Superior)**: Fixa no topo
- **Sidebar (Barra Lateral)**: Recolhível à esquerda
- **Área de Conteúdo**: Dinâmica e responsiva

```
┌─────────────────────────────────────────────────────┐
│  TopBar (Azul Escuro - Módulos)                    │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ Sidebar  │  Área de Conteúdo Principal             │
│ (Lateral)│  (Páginas, Formulários, Tabelas)        │
│          │                                          │
│ Recolhe  │                                          │
│ ◄────    │                                          │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

---

### 4.2. TopBar (Barra Superior)

**Características:**
- Posição: Fixa no topo (sticky/fixed)
- Cor de fundo: Azul escuro (`#1e3a8a` ou `blue-900`)
- Altura: 64px (h-16)
- Texto: Branco (`#ffffff`)
- Z-index: Alto (acima de outros elementos)

**Conteúdo:**
- Logo/Nome do sistema (esquerda)
- **Módulos principais** (centro/direita):
  - Gestão
  - Importar
  - Correção
  - Analista
  - Cálculos
  - Relatórios
- Informações do usuário (extrema direita)
- Botão de logout

**Exemplo de Estrutura:**
```typescript
<TopBar className="bg-blue-900 text-white h-16 fixed top-0 w-full z-50">
  <Logo />
  <NavModules>
    <NavItem href="/gestao">Gestão</NavItem>
    <NavItem href="/importar">Importar</NavItem>
    <NavItem href="/correcao">Correção</NavItem>
    <NavItem href="/analista">Analista</NavItem>
    <NavItem href="/calculos">Cálculos</NavItem>
    <NavItem href="/relatorios">Relatórios</NavItem>
  </NavModules>
  <UserInfo />
  <LogoutButton />
</TopBar>
```

**Estados dos Itens de Navegação:**
- **Default**: Texto branco, sem fundo
- **Hover**: Fundo azul mais claro (`bg-blue-800`)
- **Active (Página atual)**: Fundo azul claro + borda inferior branca
- **Disabled**: Texto cinza claro, não clicável

**Tokens Semânticos:**
- `color.topbar.bg`: Azul escuro principal
- `color.topbar.text`: Branco
- `color.topbar.hover`: Azul 800
- `color.topbar.active`: Azul 700

---

### 4.3. Sidebar (Barra Lateral Recolhível)

**Características:**
- Posição: Fixa à esquerda
- Largura: 280px (expandida) / 64px (recolhida)
- Cor de fundo: Cinza claro (`#f3f4f6` ou `gray-100`)
- Altura: 100% (abaixo da TopBar)
- Transição: Suave (300ms)

**Funcionalidade:**
- **Botão Toggle**: Ícone de menu (☰) no topo da sidebar
- **Estado Expandido**: Mostra texto + ícones
- **Estado Recolhido**: Mostra apenas ícones (com tooltip)
- **Persistência**: Estado salvo em localStorage

**Conteúdo (Hierárquico):**

1. **Ferramentas por Módulo**

**Gestão:**
- Clientes
- Termos Filtráveis
- Bandeiras
- Taxas
- Formas de Pagamento

**Importar:**
- Importar Vendas
- Importar Recebíveis
- De-Para (Mapeamento)
- Histórico de Importações

**Correção:**
- Vendas Processadas
- Vendas Filtradas
- Vendas Diversas
- Corrigir Importação

**Analista:**
- Nova Análise
- Análises Salvas
- Bandeiras
- Formas de Pagamento
- Períodos

**Cálculos:**
- Executar Cálculo
- Histórico de Cálculos
- Configurações de Taxa

**Relatórios:**
- Relatório Mensal
- Relatório Sintético
- Relatório Detalhado
- Exportar para Excel

**Exemplo de Estrutura:**
```typescript
<Sidebar 
  isCollapsed={isCollapsed}
  className={`
    fixed left-0 top-16 h-[calc(100vh-4rem)]
    transition-all duration-300 bg-gray-100
    ${isCollapsed ? 'w-16' : 'w-70'}
  `}
>
  <ToggleButton onClick={() => setIsCollapsed(!isCollapsed)}>
    {isCollapsed ? '☰' : '◄'}
  </ToggleButton>

  <SidebarSection title="Gestão" icon="settings">
    <SidebarItem href="/gestao/clientes" icon="users">
      {!isCollapsed && 'Clientes'}
    </SidebarItem>
    <SidebarItem href="/gestao/termos" icon="filter">
      {!isCollapsed && 'Termos Filtráveis'}
    </SidebarItem>
    {/* ... mais itens ... */}
  </SidebarSection>

  <SidebarSection title="Importar" icon="upload">
    <SidebarItem href="/importar/vendas" icon="receipt">
      {!isCollapsed && 'Importar Vendas'}
    </SidebarItem>
    {/* ... mais itens ... */}
  </SidebarSection>

  {/* ... outras seções ... */}
</Sidebar>
```

**Estados dos Itens da Sidebar:**
- **Default**: Texto cinza escuro, ícone cinza
- **Hover**: Fundo cinza mais escuro
- **Active (Página atual)**: Fundo azul claro, texto azul escuro, borda esquerda azul
- **Disabled**: Texto cinza claro, não clicável

**Tokens Semânticos:**
- `sidebar.width.expanded`: 280px
- `sidebar.width.collapsed`: 64px
- `sidebar.bg`: gray-100
- `sidebar.item.hover`: gray-200
- `sidebar.item.active.bg`: blue-50
- `sidebar.item.active.border`: blue-600

**Comportamento Responsivo:**
- **Desktop (> 1024px)**: Sidebar sempre visível
- **Tablet (768px - 1024px)**: Sidebar recolhida por padrão
- **Mobile (< 768px)**: Sidebar como overlay (drawer) que fecha ao clicar fora

---

### 4.4. Área de Conteúdo Principal

**Características:**
- Posição: Abaixo da TopBar, à direita da Sidebar
- Margem superior: 64px (altura da TopBar)
- Margem esquerda: 280px (expandida) / 64px (recolhida)
- Padding: 24px (p-6)
- Fundo: Branco ou cinza muito claro

**Estrutura Padrão:**
```typescript
<MainContent 
  className={`
    ml-${sidebarWidth} mt-16 p-6
    min-h-[calc(100vh-4rem)] bg-gray-50
  `}
>
  <PageHeader>
    <Breadcrumb />
    <PageTitle />
    <PageActions />
  </PageHeader>

  <PageBody>
    {/* Conteúdo dinâmico da página */}
  </PageBody>
</MainContent>
```

---

### 4.5. Breadcrumb (Migalhas de Pão)

**Sempre presente** na área de conteúdo para orientação:

```typescript
<Breadcrumb>
  <BreadcrumbItem href="/">Início</BreadcrumbItem>
  <BreadcrumbItem href="/gestao">Gestão</BreadcrumbItem>
  <BreadcrumbItem current>Termos Filtráveis</BreadcrumbItem>
</Breadcrumb>
```

**Renderização:**
- Início > Gestão > Termos Filtráveis
- Último item não é link (página atual)

---

### 4.6. Tokens de Layout

```typescript
// Cores
layout.topbar.bg = '#1e3a8a'      // blue-900
layout.topbar.text = '#ffffff'
layout.topbar.hover = '#1e40af'   // blue-800
layout.sidebar.bg = '#f3f4f6'     // gray-100
layout.content.bg = '#ffffff'

// Dimensões
layout.topbar.height = '64px'
layout.sidebar.width.expanded = '280px'
layout.sidebar.width.collapsed = '64px'
layout.content.padding = '24px'

// Z-index
layout.topbar.zIndex = 50
layout.sidebar.zIndex = 40
layout.overlay.zIndex = 30
```

---

### 4.7. Exemplo Completo de Página

```typescript
export default function TermosPage() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <>
      {/* TopBar Fixa */}
      <TopBar>
        <Logo>Financial </Logo>
        <NavModules>
          <NavItem href="/gestao" active>Gestão</NavItem>
          <NavItem href="/importar">Importar</NavItem>
          <NavItem href="/correcao">Correção</NavItem>
          <NavItem href="/analista">Analista</NavItem>
          <NavItem href="/calculos">Cálculos</NavItem>
          <NavItem href="/relatorios">Relatórios</NavItem>
        </NavModules>
        <UserInfo name="João Silva" />
      </TopBar>

      {/* Sidebar Recolhível */}
      <Sidebar isCollapsed={sidebarCollapsed}>
        <ToggleButton onClick={() => setSidebarCollapsed(!sidebarCollapsed)} />
        
        <SidebarSection title="Gestão">
          <SidebarItem href="/gestao/clientes" icon="users">
            Clientes
          </SidebarItem>
          <SidebarItem href="/gestao/termos" icon="filter" active>
            Termos Filtráveis
          </SidebarItem>
          <SidebarItem href="/gestao/bandeiras" icon="credit-card">
            Bandeiras
          </SidebarItem>
        </SidebarSection>
      </Sidebar>

      {/* Área de Conteúdo */}
      <MainContent sidebarCollapsed={sidebarCollapsed}>
        <Breadcrumb>
          <BreadcrumbItem href="/">Início</BreadcrumbItem>
          <BreadcrumbItem href="/gestao">Gestão</BreadcrumbItem>
          <BreadcrumbItem current>Termos Filtráveis</BreadcrumbItem>
        </Breadcrumb>

        <PageHeader>
          <PageTitle>Gestão de Termos Filtráveis</PageTitle>
          <PageDescription>
            Configure termos que serão usados para filtrar transações
          </PageDescription>
        </PageHeader>

        <PageBody>
          {/* Conteúdo da página */}
          <TermosFiltravelisForm />
        </PageBody>
      </MainContent>
    </>
  );
}
```

---

## 5. PADRÕES DE TELAS

### Formulário
- Título
- Inputs
- Alert informativo
- Botão primary
- Botão secondary

### Processamento
- Stepper
- Status
- Botões desabilitados
- Alert final

### Resultado
- Card
- Tabela
- Download

---

## 5. ACESSIBILIDADE

- Focus visível
- Labels associados
- aria-label quando necessário
- Não depender apenas de cor

---

## 6. REGRAS PARA AGENTS

- Mapear componentes antes do JSX
- Escolher variante + estado
- Usar tokens semânticos
- Documentar novos componentes antes de criar

---

## 7. STATUS

Design System: ATIVO  
Uso: OBRIGATÓRIO  
