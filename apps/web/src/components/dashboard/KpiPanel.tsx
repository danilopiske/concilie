'use client';

import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  DollarSign,
  FileText,
  Shield,
  Upload,
  Users,
} from 'lucide-react';
import { DashboardKpis, dashboardApi } from '@/lib/api/dashboard';

interface KpiItemProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  colorClass: string;
  bgClass: string;
}

function KpiItem({ title, value, icon, colorClass, bgClass }: KpiItemProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center gap-4">
      <div className={`flex-shrink-0 w-11 h-11 rounded-lg flex items-center justify-center ${bgClass}`}>
        <span className={colorClass}>{icon}</span>
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 truncate">{title}</p>
        <p className="text-xl font-bold text-gray-800 truncate">{value}</p>
      </div>
    </div>
  );
}

function formatCurrency(v: number) {
  return v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

function formatPercent(v: number) {
  return `${(v * 100).toFixed(2)}%`;
}

export function KpiPanel() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboardApi
      .getKpis()
      .then(setKpis)
      .catch(() => setKpis(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!kpis) return null;

  const items: KpiItemProps[] = [
    {
      title: 'Clientes',
      value: kpis.total_clientes.toLocaleString('pt-BR'),
      icon: <Users className="w-5 h-5" />,
      colorClass: 'text-blue-600',
      bgClass: 'bg-blue-50',
    },
    {
      title: 'Vendas no mês',
      value: formatCurrency(kpis.valor_total_vendas_mes),
      icon: <DollarSign className="w-5 h-5" />,
      colorClass: 'text-green-600',
      bgClass: 'bg-green-50',
    },
    {
      title: 'Contestações abertas',
      value: kpis.total_contestacoes_abertas.toLocaleString('pt-BR'),
      icon: <FileText className="w-5 h-5" />,
      colorClass: 'text-yellow-600',
      bgClass: 'bg-yellow-50',
    },
    {
      title: 'Divergências abertas',
      value: kpis.total_divergencias_abertas.toLocaleString('pt-BR'),
      icon: <AlertTriangle className="w-5 h-5" />,
      colorClass: 'text-red-600',
      bgClass: 'bg-red-50',
    },
    {
      title: 'Abusividades críticas',
      value: kpis.total_abusividades_criticas.toLocaleString('pt-BR'),
      icon: <Shield className="w-5 h-5" />,
      colorClass: 'text-purple-600',
      bgClass: 'bg-purple-50',
    },
    {
      title: 'Processamentos no mês',
      value: kpis.processamentos_mes.toLocaleString('pt-BR'),
      icon: <Upload className="w-5 h-5" />,
      colorClass: 'text-gray-600',
      bgClass: 'bg-gray-100',
    },
  ];

  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
        KPIs Executivos — {new Date().toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {items.map((item) => (
          <KpiItem key={item.title} {...item} />
        ))}
      </div>
    </div>
  );
}
