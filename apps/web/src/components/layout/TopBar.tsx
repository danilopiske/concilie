/**
 * TopBar - Executive Navy + Gold Brand
 * Gradiente navy com barra dourada e logo profissional
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { CircleCheck, LogOut } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { NotificacaoBell } from './NotificacaoBell';

interface NavItem {
  label: string;
  href: string;
}

const NAV_MODULES: NavItem[] = [
  { label: 'Home', href: '/' },
  { label: 'Gestão', href: '/gestao' },
  { label: 'Importar', href: '/importar' },
  { label: 'Análise', href: '/analise-correcoes' },
  { label: 'Cálculos', href: '/calculos' },
  { label: 'Relatórios', href: '/relatorios' },
  { label: 'Conversor', href: '/conversor' },
  { label: 'Config', href: '/configuracoes' },
];

export function TopBar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  const isActive = (href: string) => pathname.startsWith(href);

  return (
    <header className="fixed top-0 left-0 right-0 h-16 z-50 shadow-lg">
      {/* Navy Gradient Background */}
      <div className="h-full bg-gradient-to-r from-[#1e3a8a] via-[#2563eb] to-[#1e40af]">
        <div className="h-full flex items-center justify-between px-6">
          {/* Logo/Nome do Sistema */}
          <Link 
            href="/" 
            className="flex items-center gap-3 hover:opacity-90 transition-opacity"
          >
            {/* Gold Logo Icon */}
            <div className="relative">
              <div className="absolute inset-0 bg-[#f59e0b] rounded-full blur-md opacity-40" />
              <div className="relative bg-white/10 p-1.5 rounded-full backdrop-blur-sm">
                <CircleCheck className="w-7 h-7 text-[#f59e0b] stroke-[2.5]" />
              </div>
            </div>
            
            <span className="text-xl font-bold text-white tracking-wide" style={{ fontFamily: '"Poppins", sans-serif' }}>
              FINANCIAL
            </span>
          </Link>

          {/* Módulos Principais */}
          <nav className="flex items-center gap-1">
            {NAV_MODULES.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`
                  relative px-4 py-2 rounded-md transition-all duration-200 text-sm font-medium
                  ${isActive(item.href)
                    ? 'text-white'
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                  }
                `}
              >
                {item.label}
                {/* Gold Bottom Border for Active */}
                {isActive(item.href) && (
                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-[#f59e0b] rounded-full" />
                )}
              </Link>
            ))}
          </nav>

          {/* User Info + Logout */}
          <div className="flex items-center gap-4">
            <NotificacaoBell />
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-medium text-white">{user?.usuario || 'Admin'}</p>
                <p className="text-xs text-white/60">Administrador</p>
              </div>
              <div className="w-9 h-9 bg-[#f59e0b] rounded-full flex items-center justify-center text-white font-bold text-sm">
                {(user?.usuario || 'A')[0].toUpperCase()}
              </div>
            </div>
            
            <button
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-lg transition-all duration-200 text-white text-sm font-medium"
              onClick={logout}
            >
              <LogOut className="w-4 h-4" />
              Sair
            </button>
          </div>
        </div>
      </div>
      
      {/* Gold Accent Bar */}
      <div className="h-1 bg-gradient-to-r from-[#f59e0b] via-[#fbbf24] to-[#f59e0b]" />
    </header>
  );
}
