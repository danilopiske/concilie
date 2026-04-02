/**
 * Sidebar - Executive Style with Gold Accents
 * Barra lateral com destaque dourado no item ativo
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { usePermissoes } from '@/hooks/usePermissoes';
import {
  ChevronLeft,
  ChevronRight,
  User,
  Users,
  Filter,
  CreditCard,
  DollarSign,
  Upload,
  FileText,
  History,
  Edit,
  BarChart3,
  Calculator,
  Settings,
  FileBarChart,
  AlertTriangle,
  LayoutDashboard,
  Bell,
  Activity,
  Shield,
  TrendingUp,
} from 'lucide-react';

interface SidebarItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface SidebarSection {
  title: string;
  items: SidebarItem[];
  modulePrefix: string;
  modulo: string; // chave para verificação de permissão
}

const SIDEBAR_SECTIONS: SidebarSection[] = [
  {
    title: 'Gestão',
    modulePrefix: '/gestao',
    modulo: 'gestao',
    items: [
      { label: 'Clientes', href: '/gestao/clientes', icon: Users },
      { label: 'Contextos', href: '/gestao/contextos', icon: Settings },
      { label: 'Termos Filtráveis', href: '/gestao/termos', icon: Filter },
      { label: 'Bandeiras', href: '/gestao/bandeiras', icon: CreditCard },
      { label: 'Bandeiras por EC', href: '/gestao/bandeiras-ec', icon: CreditCard },
      { label: 'Taxas', href: '/gestao/taxas', icon: DollarSign },
      { label: 'Recuperação Financeira', href: '/gestao/recuperacao', icon: TrendingUp },
      { label: 'Divergências', href: '/gestao/divergencias', icon: AlertTriangle },
    ],
  },
  {
    title: 'Importar',
    modulePrefix: '/importar',
    modulo: 'importar',
    items: [
      { label: 'Importar Vendas', href: '/importar/vendas', icon: Upload },
      { label: 'De-Para', href: '/importar/de-para', icon: FileText },
      { label: 'Gestão de Processamentos', href: '/importar/processamentos', icon: History },
    ],
  },
  {
    title: 'Análise e Correções',
    modulePrefix: '/analise-correcoes',
    modulo: 'analise',
    items: [
      { label: 'Análise', href: '/analise-correcoes/analise', icon: BarChart3 },
      { label: 'Correção', href: '/analise-correcoes/correcao', icon: Edit },
      { label: 'Análise Filtrada', href: '/analise-correcoes/analise-filtrada', icon: Filter },
      { label: 'Correção Filtrada', href: '/analise-correcoes/correcao-filtrada', icon: AlertTriangle },
    ],
  },
  {
    title: 'Abusividade',
    modulePrefix: '/abusividade',
    modulo: 'analise',
    items: [
      { label: 'Abusividade', href: '/abusividade', icon: AlertTriangle },
    ],
  },
  {
    title: 'Contestação',
    modulePrefix: '/contestacoes',
    modulo: 'analise',
    items: [
      { label: 'Contestações', href: '/contestacoes', icon: FileText },
      { label: 'Métricas', href: '/gestao/contestacoes-metricas', icon: BarChart3 },
    ],
  },
  {
    title: 'Cálculos',
    modulePrefix: '/calculos',
    modulo: 'calculos',
    items: [
      { label: 'Cálculo de Taxas', href: '/calculos', icon: Calculator },
      { label: 'Gestão de Cálculos', href: '/calculos/gestao', icon: History },
    ],
  },
  {
    title: 'Relatórios',
    modulePrefix: '/relatorios',
    modulo: 'relatorios',
    items: [
      { label: 'Gerar Relatórios', href: '/relatorios', icon: FileBarChart },
      { label: 'Gestão de Relatórios', href: '/relatorios/gestao', icon: History },
    ],
  },
  {
    title: 'Configurações',
    modulePrefix: '/configuracoes',
    modulo: 'configuracoes',
    items: [
      { label: 'Usuários', href: '/configuracoes/usuarios', icon: Users },
      { label: 'Meu Perfil', href: '/configuracoes/perfil', icon: User },
      { label: 'Auditoria', href: '/configuracoes/auditoria', icon: Shield },
      { label: 'Alertas', href: '/configuracoes/alertas', icon: Bell },
    ],
  },
  {
    title: 'Notificações',
    modulePrefix: '/notificacoes',
    modulo: 'dashboard',
    items: [
      { label: 'Centro de Alertas', href: '/notificacoes', icon: Bell },
    ],
  },
  {
    title: 'Centro de Tarefas',
    modulePrefix: '/tarefas',
    modulo: 'dashboard',
    items: [
      { label: 'Progresso de Tarefas', href: '/tarefas', icon: Activity },
    ],
  },
  {
    title: 'Sistema',
    modulePrefix: '/status',
    modulo: 'dashboard',
    items: [
      { label: 'Status do Sistema', href: '/status', icon: Activity },
    ],
  },
];

const STORAGE_KEY = 'sidebar-collapsed';

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === 'true';
  });
  const pathname = usePathname();
  const { podeAcessar } = usePermissoes();

  // Persistir estado
  const toggleCollapsed = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem(STORAGE_KEY, String(newState));
  };

  // Verificar se o módulo está ativo
  const isModuleActive = (modulePrefix: string) => pathname.startsWith(modulePrefix);

  // Verificar se o item está ativo
  const isItemActive = (href: string) => pathname === href;

  // Determine active section based on current path (only if user has access)
  const activeSection = SIDEBAR_SECTIONS.find(
    section => isModuleActive(section.modulePrefix) && podeAcessar(section.modulo)
  );

  return (
    <aside
      className={`
        fixed left-0 top-[68px] h-[calc(100vh-68px)]
        bg-white border-r border-gray-200 shadow-sm
        transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-16' : 'w-[280px]'}
        z-40 overflow-y-auto
      `}
    >
      {/* Toggle Button */}
      <button
        onClick={toggleCollapsed}
        className="w-full h-12 flex items-center justify-center border-b border-gray-200 hover:bg-gray-50 transition-colors group"
        aria-label={isCollapsed ? 'Expandir menu' : 'Recolher menu'}
      >
        {isCollapsed ? (
          <ChevronRight className="w-5 h-5 text-[#1e3a8a] group-hover:text-[#f59e0b] transition-colors" />
        ) : (
          <ChevronLeft className="w-5 h-5 text-[#1e3a8a] group-hover:text-[#f59e0b] transition-colors" />
        )}
      </button>

      {/* Dashboard Link — always visible */}
      <div className="px-2 pt-3 pb-1 border-b border-gray-100">
        <Link
          href="/dashboard"
          className={`
            relative flex items-center gap-3 px-3 py-2.5 rounded-lg
            transition-all duration-200
            ${isItemActive('/dashboard')
              ? 'bg-gradient-to-r from-[#fef3c7] to-transparent text-[#1e3a8a] font-medium shadow-sm'
              : 'text-gray-700 hover:bg-gray-50 hover:text-[#1e3a8a]'
            }
            ${isCollapsed ? 'justify-center' : ''}
          `}
          title={isCollapsed ? 'Dashboard' : undefined}
        >
          {isItemActive('/dashboard') && (
            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-[#f59e0b] to-[#fbbf24] rounded-r-full" />
          )}
          <LayoutDashboard className={`w-5 h-5 ${isItemActive('/dashboard') ? 'text-[#f59e0b]' : 'text-gray-500'} flex-shrink-0`} />
          {!isCollapsed && <span className="text-sm">Dashboard</span>}
        </Link>
      </div>

      {/* Contextual Tools */}
      <nav className="py-4">
        {activeSection ? (
           <div className="mb-2">
              {/* Section Title */}
              {!isCollapsed && (
                <h3 className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  {activeSection.title}
                </h3>
              )}

              {/* Items */}
              <div className="space-y-1 px-2">
                {activeSection.items.map((item) => {
                  const Icon = item.icon;
                  const active = isItemActive(item.href);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`
                        relative flex items-center gap-3 px-3 py-2.5 rounded-lg
                        transition-all duration-200
                        ${active
                          ? 'bg-gradient-to-r from-[#fef3c7] to-transparent text-[#1e3a8a] font-medium shadow-sm'
                          : 'text-gray-700 hover:bg-gray-50 hover:text-[#1e3a8a]'
                        }
                        ${isCollapsed ? 'justify-center' : ''}
                      `}
                      title={isCollapsed ? item.label : undefined}
                    >
                      {/* Gold Left Border for Active */}
                      {active && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-[#f59e0b] to-[#fbbf24] rounded-r-full" />
                      )}
                      
                      <Icon className={`w-5 h-5 ${active ? 'text-[#f59e0b]' : 'text-gray-500'} flex-shrink-0`} />
                      
                      {!isCollapsed && (
                        <span className="text-sm">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
        ) : (
            // Fallback for Dashboard Home or unknown routes
            !isCollapsed && (
                <div className="px-6 py-4 text-sm text-gray-500 text-center">
                    Selecione um módulo na barra superior
                </div>
            )
        )}
      </nav>
    </aside>
  );
}
