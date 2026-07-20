import React, { useEffect, useState, useCallback, useRef } from 'react';
import Link from 'next/link';
import { Table, TableColumn } from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Download, RefreshCw, FileText, AlertCircle, Loader2, Clock, Pencil } from 'lucide-react';
import { relatorioApi, RelatorioTask } from '@/lib/api/relatorio';

const AUTO_REFRESH_INTERVAL_MS = 15000;
const ACTIVE_STATUSES = ['PENDING', 'PROCESSING'];

interface RelatorioHistoryProps {
  processamentoId?: string;
  refreshTrigger?: number;
}

export function RelatorioHistory({ processamentoId, refreshTrigger }: RelatorioHistoryProps) {
  const [history, setHistory] = useState<RelatorioTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState('');
  const [filterTipo, setFilterTipo] = useState('');
  const autoRefreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchHistory = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      const data = await relatorioApi.getHistorico(processamentoId, 0, 50, filterStatus || undefined, filterTipo || undefined);
      setHistory(data);
    } catch (err) {
      console.error('Erro ao buscar histórico:', err);
      setError('Não foi possível carregar o histórico de relatórios.');
    } finally {
      if (!silent) setLoading(false);
    }
  }, [processamentoId, filterStatus, filterTipo]);

  // Start/stop auto-refresh based on active tasks
  useEffect(() => {
    const hasActiveTasks = history.some(t => ACTIVE_STATUSES.includes(t.status.toUpperCase()));

    if (hasActiveTasks) {
      autoRefreshRef.current = setInterval(() => {
        fetchHistory(true);
      }, AUTO_REFRESH_INTERVAL_MS);
    } else {
      if (autoRefreshRef.current) {
        clearInterval(autoRefreshRef.current);
        autoRefreshRef.current = null;
      }
    }

    return () => {
      if (autoRefreshRef.current) {
        clearInterval(autoRefreshRef.current);
        autoRefreshRef.current = null;
      }
    };
  }, [history, fetchHistory]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory, refreshTrigger]);

  const handleDownload = (path: string) => {
    if (!path) return;
    const url = relatorioApi.downloadUrl(path);
    window.open(url, '_blank');
  };

  const getStatusBadge = (status: string) => {
    const s = status.toUpperCase();
    switch (s) {
      case 'SUCCESS':
      case 'COMPLETED':
        return <Badge variant="success">Concluído</Badge>;
      case 'PROCESSING':
        return <Badge variant="info" className="animate-pulse">Processando</Badge>;
      case 'PENDING':
        return <Badge variant="info" className="animate-pulse">Pendente</Badge>;
      case 'FAILED':
        return <Badge variant="error">Erro</Badge>;
      default:
        return <Badge variant="default">{status}</Badge>;
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
      return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date(dateStr));
    } catch (e) {
      return dateStr;
    }
  };

  const hasActiveTasks = history.some(t => ACTIVE_STATUSES.includes(t.status.toUpperCase()));

  const columns: TableColumn<RelatorioTask>[] = [
    {
      key: 'id',
      label: 'ID',
      render: (val) => (
        <span className="text-xs font-mono text-gray-400" title={val}>
          {String(val).slice(0, 8)}…
        </span>
      )
    },
    {
      key: 'updated_at',
      label: 'Data/Hora',
      render: (val) => (
        <span className="text-sm font-semibold text-gray-700">
          {formatDate(val)}
        </span>
      )
    },
    {
      key: 'tipo_relatorio',
      label: 'Tipo',
      render: (val) => (
        <span className="text-sm text-gray-600 capitalize">
          {val ?? '-'}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (val) => getStatusBadge(val)
    },
    {
      key: 'metadata',
      label: 'Adquirente',
      render: (val) => (
        <span className="text-sm text-gray-500 italic">
          {(val as Record<string, unknown>)?.adquirente as string || 'Geral'}
        </span>
      )
    },
    {
      key: 'actions',
      label: '',
      width: '180px',
      render: (_, row) => (
        <div className="flex justify-end gap-2">
          {row.status === 'SUCCESS' && (
            <Link href={`/relatorios/editor?task_id=${row.id}`}>
              <Button size="sm" variant="secondary" className="rounded-xl h-8 px-3 font-bold text-xs">
                <Pencil className="h-3 w-3 mr-1" />
                EDITAR
              </Button>
            </Link>
          )}
          {row.status === 'SUCCESS' && row.result_path && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => handleDownload(row.result_path!)}
              className="rounded-xl h-8 px-4 font-bold text-xs"
            >
              <Download className="h-3 w-3 mr-2" />
              BAIXAR
            </Button>
          )}
          {row.status === 'SUCCESS' && row.id && (
            <a
              href={relatorioApi.taskDownloadUrl(row.id, 'pdf')}
              target="_blank"
              rel="noreferrer"
            >
              <Button size="sm" variant="secondary" className="rounded-xl h-8 px-3 font-bold text-xs">
                <FileText className="h-3 w-3 mr-1" />
                PDF
              </Button>
            </a>
          )}
        </div>
      )
    }
  ];

  if (loading && history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-gray-500 font-medium">Carregando histórico...</p>
      </div>
    );
  }

  if (error && history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4 border border-red-100 bg-red-50 rounded-2xl">
        <AlertCircle className="h-8 w-8 text-red-500" />
        <p className="text-red-700 font-bold">{error}</p>
        <Button onClick={() => fetchHistory()} variant="secondary" size="sm">
          Tentar novamente
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Clock className="w-4 h-4 text-primary" />
          </div>
          <h3 className="text-lg font-bold text-gray-800">Últimos Relatórios</h3>
          {hasActiveTasks && (
            <span className="ml-2 inline-flex items-center gap-1 text-xs text-blue-600 font-medium">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Auto-atualizando…
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Status filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">Todos os status</option>
            <option value="PENDING">Pendente</option>
            <option value="PROCESSING">Processando</option>
            <option value="SUCCESS">Concluído</option>
            <option value="FAILED">Erro</option>
          </select>

          {/* Tipo filter */}
          <select
            value={filterTipo}
            onChange={(e) => setFilterTipo(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 bg-white focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">Todos os tipos</option>
            <option value="mensal">Mensal</option>
            <option value="retroativo">Retroativo</option>
            <option value="abusividade">Abusividade</option>
          </select>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchHistory()}
            disabled={loading}
            className="text-gray-500 hover:text-primary transition-colors font-semibold"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Sincronizar
          </Button>
        </div>
      </div>

      {history.length === 0 ? (
        <div className="text-center py-16 border-2 border-dashed border-gray-100 rounded-3xl bg-gray-50/30">
          <FileText className="h-16 w-16 text-gray-200 mx-auto mb-4" />
          <p className="text-gray-400 font-medium">Nenhum relatório encontrado no histórico.</p>
        </div>
      ) : (
        <Table
          data={history}
          columns={columns}
          pagination={true}
          pageSize={10}
        />
      )}
    </div>
  );
}
