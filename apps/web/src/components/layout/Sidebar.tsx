/**
 * Sidebar - Barra Lateral Recolhível
 * Com ferramentas organizadas por módulo
 */

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  ChevronLeft, 
  ChevronRight,
  Users,
  Filter,
  CreditCard,
  DollarSign,
  Wallet,
  Upload,
  FileText,
  History,
  Edit,
  BarChart3,
  Calculator,
  Settings,
  FileBarChart
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
}

const SIDEBAR_SECTIONS: SidebarSection[] = [
  {
    title: 'Gestão',
    modulePrefix: '/gestao',
    items: [
      { label: 'Clientes', href: '/gestao/clientes', icon: Users },
      { label: 'Contextos', href: '/gestao/contextos', icon: Settings },
      { label: 'Termos Filtráveis', href: '/gestao/termos', icon: Filter },
      { label: 'Bandeiras', href: '/gestao/bandeiras', icon: CreditCard },
      { label: 'Bandeiras por EC', href: '/gestao/bandeiras-ec', icon: CreditCard },
      { label: 'Taxas', href: '/gestao/taxas', icon: DollarSign },
    ],
  },
  {
    title: 'Importar',
    modulePrefix: '/importar',
    items: [
      { label: 'Importar Vendas', href: '/importar/vendas', icon: Upload },
      { label: 'De-Para', href: '/importar/de-para', icon: FileText },
      { label: 'Gestão de Processamentos', href: '/importar/processamentos', icon: History },
    ],
  },
  {
    title: 'Análise e Correções',
    modulePrefix: '/analise-correcoes',
    items: [
      { label: 'Análise', href: '/analise-correcoes/analise', icon: BarChart3 },
      { label: 'Correção', href: '/analise-correcoes/correcao', icon: Edit },
    ],
  },
  {
    title: 'Cálculos',
    modulePrefix: '/calculos',
    items: [
      { label: 'Cálculo de Taxas', href: '/calculos', icon: Calculator },
    ],
  },
  {
    title: 'Relatórios',
    modulePrefix: '/relatorios',
    items: [
      { label: 'Gerar Relatórios', href: '/relatorios', icon: FileBarChart },
    ],
  },
  {
    title: 'Configurações',
    modulePrefix: '/configuracoes',
    items: [
      { label: 'Usuários', href: '/configuracoes/usuarios', icon: Users },
    ],
  },
];

const STORAGE_KEY = 'sidebar-collapsed';

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

  // Restaurar estado do localStorage
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) {
      setIsCollapsed(saved === 'true');
    }
  }, []);

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

  // Determine active section based on current path
  const activeSection = SIDEBAR_SECTIONS.find(section => isModuleActive(section.modulePrefix));

  return (
    <aside
      className={`
        fixed left-0 top-16 h-[calc(100vh-4rem)]
        bg-gray-100 border-r border-gray-200
        transition-all duration-300 ease-in-out
        ${isCollapsed ? 'w-16' : 'w-[280px]'}
        z-40 overflow-y-auto
      `}
    >
      {/* Toggle Button */}
      <button
        onClick={toggleCollapsed}
        className="w-full h-12 flex items-center justify-center border-b border-gray-200 hover:bg-gray-200 transition-colors"
        aria-label={isCollapsed ? 'Expandir menu' : 'Recolher menu'}
      >
        {isCollapsed ? (
          <ChevronRight className="w-5 h-5 text-gray-600" />
        ) : (
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        )}
      </button>

      {/* Contextual Tools */}
      <nav className="py-4">
        {activeSection ? (
           <div className="mb-2">
              {/* Section Title (Optional, can be removed if TopBar is sufficient context) */}
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
                        flex items-center gap-3 px-3 py-2 rounded-md
                        transition-all duration-200
                        ${active
                          ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-600'
                          : 'text-gray-700 hover:bg-gray-200'
                        }
                        ${isCollapsed ? 'justify-center' : ''}
                      `}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <Icon className={`w-5 h-5 ${active ? 'text-blue-600' : 'text-gray-500'}`} />
                      {!isCollapsed && (
                        <span className="text-sm font-medium">{item.label}</span>
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
