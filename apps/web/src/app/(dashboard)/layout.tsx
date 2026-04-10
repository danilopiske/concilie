/**
 * Dashboard Layout
 * Aplica TopBar + Sidebar para todas as páginas do dashboard
 */

'use client';

import { TopBar, Sidebar } from '@/components/layout';
import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Loading } from '@/components/shared/Loading';
import { useRouter } from 'next/navigation';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { user, loading } = useAuth();
  const router = useRouter();

  // Auth enforcement
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  // Sincronizar estado do sidebar e marcar como montado
  useEffect(() => {
    setMounted(true);
    
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

  if (loading || !mounted) {
      return (
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
              <Loading />
          </div>
      );
  }

  if (!user) return null; // Will redirect

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
