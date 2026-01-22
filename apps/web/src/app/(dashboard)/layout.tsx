/**
 * Dashboard Layout
 * Aplica TopBar + Sidebar para todas as páginas do dashboard
 */

'use client';

import { TopBar, Sidebar } from '@/components/layout';
import { useState, useEffect } from 'react';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Sincronizar estado do sidebar (ouvir mudanças no localStorage)
  useEffect(() => {
    const handleStorageChange = () => {
      const saved = localStorage.getItem('sidebar-collapsed');
      if (saved !== null) {
        setSidebarCollapsed(saved === 'true');
      }
    };

    // Listener para mudanças
    window.addEventListener('storage', handleStorageChange);
    
    // Estado inicial
    handleStorageChange();

    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* TopBar Fixa */}
      <TopBar />

      {/* Sidebar Recolhível */}
      <Sidebar />

      {/* Área de Conteúdo Principal */}
      <main
        className={`
          pt-16
          transition-all duration-300
          ${sidebarCollapsed ? 'ml-16' : 'ml-[280px]'}
          min-h-[calc(100vh-4rem)]
        `}
      >
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
