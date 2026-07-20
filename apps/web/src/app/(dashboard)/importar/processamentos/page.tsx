'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Table, TableColumn } from '@/components/ui/Table';
import { Breadcrumb } from '@/components/layout/Breadcrumb';
import { Loading } from '@/components/shared/Loading';
import { ErrorMessage } from '@/components/shared/ErrorMessage';
import { importacaoApi } from '@/lib/api/importacao';
import { Processamento } from '@/lib/types/importacao';
import { Modal } from '@/components/ui/Modal';
import { clientesApi, Cliente } from '@/lib/api/clientes';
import { processamentosApi } from '@/lib/api/processamentos';
import Link from 'next/link';
import {
  Trash2,
  RefreshCw,
  FileCheck,
  Files,
  AlertCircle,
  Clock,
  Database,
  ArrowRight,
  Download
} from 'lucide-react';

interface ActiveTask {
  id: string;
  status: string;
  progress: number;
  message: string;
  updated_at: string;
  tipo_arquivo: string;
  contexto: string;
}

const PERIOD_OPTIONS = [
  { label: '7 dias', value: 7 },
  { label: '30 dias', value: 30 },
  { label: '90 dias', value: 90 },
  { label: '1 ano', value: 365 },
];

export default function ProcessamentosPage() {
  const [processamentos, setProcessamentos] = useState<Processamento[]>([]);
  const [activeTasks, setActiveTasks] = useState<ActiveTask[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [periodo, setPeriodo] = useState<number>(90);
  const [clienteId, setClienteId] = useState<number | undefined>(undefined);

  // Load clientes once
  useEffect(() => {
    clientesApi.listar().then(setClientes).catch(() => setClientes([]));
  }, []);

  // Poll for active tasks
  const fetchActiveTasks = useCallback(async () => {
    try {
      const data = await importacaoApi.getActiveTasks(1);
      setActiveTasks(data);
    } catch (err) {
      console.error("Error fetching active tasks:", err);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const data = await importacaoApi.processamentos.listar(clienteId);
      setProcessamentos(data);
    } catch (err) {
      setError('Erro ao carregar histórico de processamentos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [periodo, clienteId]);

  const refreshAll = useCallback(() => {
    fetchActiveTasks();
    fetchHistory();
  }, [fetchActiveTasks, fetchHistory]);

  useEffect(() => {
    refreshAll();
    
    // Polling interval for active tasks (every 3 seconds)
    const interval = setInterval(() => {
      fetchActiveTasks();
    }, 3000);
    
    return () => clearInterval(interval);
  }, [refreshAll, fetchActiveTasks]);

  // Re-fetch history when a task completes
  useEffect(() => {
    const hasAnyProcessing = activeTasks.some(t => t.status === 'PROCESSING' || t.status === 'PENDING');
    if (!hasAnyProcessing && activeTasks.length > 0) {
      // Just completed or no more pending, refresh history
      fetchHistory();
    }
  }, [activeTasks, fetchHistory]);

  const handleDelete = useCallback(async (id: string | number) => {
    if (!window.confirm('Tem certeza que deseja EXCLUIR este processamento? Essa ação não pode ser desfeita e removerá todas as vendas e cálculos associados.')) {
      return;
    }

    try {
      setDeletingId(String(id));
      await importacaoApi.processamentos.deletarMany([String(id)]);
      await fetchHistory();
    } catch (err) {
      console.error(err);
      alert('Erro ao deletar processamento. Verifique o console.');
    } finally {
      setDeletingId(null);
    }
  }, [fetchHistory]);

  // Memoized stats
  const stats = useMemo(() => {
    const total = processamentos.length;
    const success = processamentos.filter(p => p.status === 'Sucesso').length;
    const error = processamentos.filter(p => p.status === 'Erro').length;
    const totalRows = processamentos.reduce((acc, p) => acc + (p.linhas_processadas || 0), 0);
    
    return { total, success, error, totalRows };
  }, [processamentos]);

  const columns: TableColumn<Processamento>[] = [
    { 
      key: 'id', 
      label: 'ID', 
      width: '80px',
      render: (val) => <span className="text-gray-400 font-mono text-xs">{val}</span>
    },
    { 
      key: 'nome_arquivo', 
      label: 'Arquivo',
      render: (val, row) => (
        <div className="flex flex-col">
          <span className="font-medium text-gray-900">{val}</span>
          <span className="text-xs text-gray-500">{row.contexto || 'Geral'} • {row.ec_id || 'Global'}</span>
        </div>
      )
    },
    { 
      key: 'tipo_arquivo', 
      label: 'Layout',
      render: (val) => (
        <Badge variant="info" className="bg-blue-50 text-blue-700 border-blue-100">
          {val}
        </Badge>
      )
    },
    { 
      key: 'status', 
      label: 'Status',
      render: (value) => {
        const variants: Record<string, string> = {
          'Sucesso': 'success',
          'Erro': 'error',
          'Processando': 'warning',
          'Pendente': 'default'
        };
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return <Badge variant={(variants[String(value)] || 'default') as any}>{String(value)}</Badge>;
      }
    },
    { 
      key: 'linhas_processadas', 
      label: 'Dados',
      render: (_, row) => (
        <div className="flex flex-col">
          <span className="text-sm font-medium">{row.linhas_processadas?.toLocaleString()} linhas</span>
          {(row.linhas_erro ?? 0) > 0 && (
            <span className="text-xs text-orange-600">{row.linhas_erro?.toLocaleString()} filtradas</span>
          )}
        </div>
      )
    },
    { 
      key: 'data_inicio', 
      label: 'Processado em', 
      format: 'date' 
    },
    {
      key: 'actions',
      label: 'Ações',
      width: '120px',
      render: (_, row) => (
        <div className="flex items-center gap-1">
          <Link
            href={`/importar/processamentos/detalhes?id=${encodeURIComponent(row.id)}`}
            className="inline-flex items-center justify-center h-8 w-8 rounded text-blue-500 hover:text-blue-700 hover:bg-blue-50 transition-colors"
            title="Ver detalhes"
          >
            <ArrowRight size={16} />
          </Link>
          <Button
            variant="secondary"
            size="sm"
            className="text-red-400 hover:text-red-600 hover:bg-red-50 bg-transparent border-none shadow-none"
            onClick={() => handleDelete(row.id)}
            disabled={!!deletingId}
            title="Excluir tudo deste processamento"
          >
            {deletingId === String(row.id) ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-red-600"></div>
            ) : (
              <Trash2 size={18} />
            )}
          </Button>
        </div>
      )
    }
  ];

  return (
    <div className="max-w-7xl mx-auto pb-12">
      <Breadcrumb
        items={[
          { label: 'Importar', href: '/importar/vendas' },
          { label: 'Processamentos' },
        ]}
      />

      {/* Header */}
      <div className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-2">
            Dashboard de Processamentos
          </h1>
          <p className="text-lg text-gray-600">
            Acompanhe o status das suas importações em tempo real.
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={refreshAll}
            className="flex gap-2 items-center"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            Sincronizar
          </Button>
          <Button
            variant="primary"
            onClick={() => window.location.href = '/importar/vendas'}
            className="flex gap-2 items-center"
          >
            Nova Importação
            <ArrowRight size={18} />
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-8 flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Período:</label>
          <div className="flex gap-1">
            {PERIOD_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setPeriodo(opt.value)}
                className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                  periodo === opt.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {clientes.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-600">Cliente:</label>
            <select
              value={clienteId ?? ''}
              onChange={e => setClienteId(e.target.value ? Number(e.target.value) : undefined)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            >
              <option value="">Todos</option>
              {clientes.map(c => (
                <option key={c.cliente_id} value={c.cliente_id}>
                  {c.nome_fantasia || c.razao_social}
                </option>
              ))}
            </select>
          </div>
        )}

        <a
          href={processamentosApi.exportarCsvUrl({ cliente_id: clienteId, periodo })}
          download
          className="ml-auto inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
        >
          <Download size={16} />
          Exportar CSV
        </a>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatsCard 
          title="Total Importados" 
          value={stats.total} 
          icon={<Files className="text-blue-600" size={24} />} 
          color="blue"
        />
        <StatsCard 
          title="Linhas Processadas" 
          value={stats.totalRows.toLocaleString()} 
          icon={<Database className="text-emerald-600" size={24} />} 
          color="emerald"
        />
        <StatsCard 
          title="Concluídos com Sucesso" 
          value={stats.success} 
          icon={<FileCheck className="text-green-600" size={24} />} 
          color="green"
        />
        <StatsCard 
          title="Falhas Detectadas" 
          value={stats.error} 
          icon={<AlertCircle className="text-red-600" size={24} />} 
          color="red"
          highlight={stats.error > 0}
        />
      </div>

      {/* Active Tasks Feed */}
      {activeTasks.length > 0 && (
        <div className="mb-10">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="text-blue-600" size={20} />
            <h2 className="text-xl font-bold text-gray-800">Processamentos Ativos</h2>
            <Badge variant="info" className="ml-2">{activeTasks.length}</Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeTasks.map(task => (
              <ActiveTaskCard key={task.id} task={task} />
            ))}
          </div>
        </div>
      )}

      {error && <ErrorMessage message={error} />}

      {/* History Table */}
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-xl font-bold text-gray-800">Histórico Recente</h2>
        <span className="text-sm text-gray-400">
          — últimos {periodo} dias
          {clienteId && clientes.find(c => c.cliente_id === clienteId)
            ? ` · ${clientes.find(c => c.cliente_id === clienteId)!.nome_fantasia || clientes.find(c => c.cliente_id === clienteId)!.razao_social}`
            : ''}
        </span>
      </div>
      <Card className="overflow-hidden border-gray-100 shadow-sm hover:shadow-md transition-shadow">
        {loading ? (
          <div className="p-12">
            <Loading message="Carregando histórico de processamentos..." />
          </div>
        ) : (
          <Table
            columns={columns}
            data={processamentos}
            emptyMessage="Nenhum processamento encontrado no histórico."
          />
        )}
      </Card>

      {/* Delete Progress Modal */}
      <Modal
        isOpen={!!deletingId}
        onClose={() => {}} 
        title="Apagando Processamento"
      >
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <div className="relative mb-6">
             <div className="animate-spin rounded-full h-20 w-20 border-4 border-gray-100 border-t-red-600 shadow-inner"></div>
             <Trash2 className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-red-600 opacity-20" size={32} />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">
            Limpando Banco de Dados
          </h3>
          <p className="text-gray-500 max-w-sm mb-6">
            Estamos removendo permanentemente todos os registros vinculados a este processamento.
          </p>
          <div className="w-full bg-red-50 p-4 rounded-xl border border-red-100 flex gap-3 text-left">
            <AlertCircle className="text-red-600 shrink-0" size={20} />
            <div className="text-red-800 text-sm">
              <strong>Proceda com cautela:</strong> Para arquivos gigantescos, esta operação pode levar algum tempo para garantir a integridade dos dados.
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// Sub-components

function StatsCard({ title, value, icon, color, highlight = false }: { title: string; value: string | number; icon: React.ReactNode; color: string; highlight?: boolean }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-100',
    green: 'bg-green-50 border-green-100',
    emerald: 'bg-emerald-50 border-emerald-100',
    red: 'bg-red-50 border-red-100',
  };

  return (
    <Card className={`p-6 border ${colorMap[color] || 'border-gray-100'} shadow-sm hover:scale-[1.02] transition-transform cursor-pointer`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm font-medium text-gray-500 mb-1">{title}</p>
          <h3 className={`text-3xl font-bold ${highlight ? 'text-red-600' : 'text-gray-900'}`}>{value}</h3>
        </div>
        <div className={`p-3 rounded-xl bg-white shadow-sm border border-gray-50`}>
          {icon}
        </div>
      </div>
    </Card>
  );
}

function ActiveTaskCard({ task }: { task: ActiveTask }) {
  const isFailed = task.status === 'FAILED';
  const isFinished = task.status === 'SUCCESS';
  
  return (
    <Card className={`p-5 overflow-hidden transition-all duration-300 border-l-4 ${
      isFailed ? 'border-l-red-500' : isFinished ? 'border-l-green-500' : 'border-l-blue-500 animate-pulse-subtle'
    } shadow-sm bg-white`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isFailed ? 'bg-red-50' : 'bg-blue-50'}`}>
            <RefreshCw size={18} className={`${!isFinished && !isFailed ? 'animate-spin' : ''} ${isFailed ? 'text-red-600' : 'text-blue-600'}`} />
          </div>
          <div>
             <h4 className="font-bold text-gray-800 text-sm leading-tight">
               Importando {task.contexto}
             </h4>
             <p className="text-xs text-gray-500 mt-1">{task.message}</p>
          </div>
        </div>
        <Badge variant={isFailed ? 'error' : isFinished ? 'success' : 'info'}>
          {task.progress}%
        </Badge>
      </div>
      
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 ${
            isFailed ? 'bg-red-500' : isFinished ? 'bg-green-500' : 'bg-gradient-to-r from-blue-400 to-blue-600 shadow-[0_0_8px_rgba(37,99,235,0.4)]'
          }`}
          style={{ width: `${task.progress}%` }}
        />
      </div>
      
      <div className="flex justify-between items-center mt-3 text-[10px] text-gray-400 uppercase tracking-widest font-bold">
        <span>Tarefa: #{task.id.split('-')[0]}</span>
        <span>Modo: {task.tipo_arquivo === 'V' ? 'Vendas' : 'Recebíveis'}</span>
      </div>
    </Card>
  );
}

