/**
 * TopBar - Barra Superior Fixa
 * Azul escuro com módulos em branco
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  label: string;
  href: string;
}

const NAV_MODULES: NavItem[] = [
  { label: 'Gestão', href: '/gestao' },
  { label: 'Importar', href: '/importar' },
  { label: 'Análise e Correções', href: '/analise-correcoes' },
  { label: 'Cálculos', href: '/calculos' },
  { label: 'Relatórios', href: '/relatorios' },
  { label: 'Configurações', href: '/configuracoes' },
];

import { useAuth } from '@/hooks/useAuth';

export function TopBar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-blue-900 text-white z-50 shadow-md">
      <div className="h-full flex items-center justify-between px-6">
        {/* Logo/Nome do Sistema */}
        <Link href="/" className="flex items-center gap-2 hover:text-blue-200 transition-colors">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">C</span>
          </div>
          <span className="text-xl font-bold">
            Concilie
          </span>
        </Link>

        {/* Módulos Principais */}
        <nav className="flex items-center gap-1">
          {NAV_MODULES.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`
                px-4 py-2 rounded-md transition-all duration-200
                ${isActive(item.href)
                  ? 'bg-blue-700 border-b-2 border-white'
                  : 'hover:bg-blue-800'
                }
              `}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* User Info + Logout */}
        <div className="flex items-center gap-4">
          <span className="text-sm">{user?.usuario || 'Admin'}</span>
          <button
            className="px-3 py-1 bg-blue-800 hover:bg-blue-700 rounded transition-colors text-sm"
            onClick={logout}
          >
            Sair
          </button>
        </div>
      </div>
    </header>
  );
}
