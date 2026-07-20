'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  Bell,
  CheckCheck,
  FileBarChart,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { type Notificacao, notificacaoApi } from '@/lib/api/notificacao';

const TIPO_LABELS: Record<string, string> = {
  relatorio_ok: 'Relatório',
  relatorio_erro: 'Relatório',
  abusividade_detectada: 'Abusividade',
  importacao_ok: 'Importação',
  importacao_erro: 'Importação',
};

const TIPO_ICONS: Record<string, React.ReactNode> = {
  relatorio_ok: <FileBarChart className="w-5 h-5 text-green-500" />,
  relatorio_erro: <FileBarChart className="w-5 h-5 text-red-500" />,
  abusividade_detectada: <AlertTriangle className="w-5 h-5 text-amber-500" />,
  importacao_ok: <Upload className="w-5 h-5 text-blue-500" />,
  importacao_erro: <Upload className="w-5 h-5 text-red-500" />,
};

function tempoRelativo(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'agora';
  if (mins < 60) return `${mins} minuto${mins > 1 ? 's' : ''} atrás`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hora${hrs > 1 ? 's' : ''} atrás`;
  const days = Math.floor(hrs / 24);
  return `${days} dia${days > 1 ? 's' : ''} atrás`;
}

type FiltroTipo = 'todos' | 'nao-lidas' | string;

export default function NotificacoesPage() {
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  const [filtroStatus, setFiltroStatus] = useState<'todos' | 'nao-lidas'>('todos');
  const [filtroTipo, setFiltroTipo] = useState<FiltroTipo>('todos');
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const LIMIT = 20;

  const carregar = useCallback(
    async (reset = false) => {
      setLoading(true);
      try {
        const skip = reset ? 0 : page * LIMIT;
        const params: Record<string, unknown> = { skip, limit: LIMIT };
        if (filtroStatus === 'nao-lidas') params.lida = false;
        const data = await notificacaoApi.listar(params);
        if (reset) {
          setNotificacoes(data);
          setPage(0);
        } else {
          setNotificacoes((prev) => [...prev, ...data]);
        }
        setHasMore(data.length === LIMIT);
      } finally {
        setLoading(false);
      }
    },
    [filtroStatus, page]
  );

  useEffect(() => {
    carregar(true);
  }, [filtroStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleMarcarLida = async (id: string) => {
    await notificacaoApi.marcarLida(id);
    setNotificacoes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, lida: true } : n))
    );
  };

  const handleRemover = async (id: string) => {
    await notificacaoApi.remover(id);
    setNotificacoes((prev) => prev.filter((n) => n.id !== id));
  };

  const handleMarcarTodas = async () => {
    await notificacaoApi.marcarTodasLidas();
    setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })));
  };

  const filtradas =
    filtroTipo === 'todos'
      ? notificacoes
      : notificacoes.filter((n) => n.tipo === filtroTipo);

  const naoLidasCount = notificacoes.filter((n) => !n.lida).length;
  const tipos = [...new Set(notificacoes.map((n) => n.tipo))];

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bell className="w-6 h-6 text-[#1e3a8a]" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">Centro de Alertas</h1>
            <p className="text-sm text-gray-500">
              {naoLidasCount > 0
                ? `${naoLidasCount} não lida${naoLidasCount > 1 ? 's' : ''}`
                : 'Tudo em dia'}
            </p>
          </div>
        </div>
        {naoLidasCount > 0 && (
          <button
            onClick={handleMarcarTodas}
            className="flex items-center gap-2 px-4 py-2 bg-[#1e3a8a] text-white text-sm rounded-lg hover:bg-[#1e40af] transition-colors"
          >
            <CheckCheck className="w-4 h-4" />
            Marcar todas como lidas
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-2 mb-4">
        {/* Status */}
        <div className="flex rounded-lg border border-gray-200 overflow-hidden">
          {(['todos', 'nao-lidas'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setFiltroStatus(s)}
              className={`px-3 py-1.5 text-sm transition-colors ${
                filtroStatus === s
                  ? 'bg-[#1e3a8a] text-white'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              {s === 'todos' ? 'Todos' : 'Não lidas'}
            </button>
          ))}
        </div>

        {/* Tipo */}
        {tipos.length > 1 && (
          <div className="flex flex-wrap gap-1">
            <button
              onClick={() => setFiltroTipo('todos')}
              className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                filtroTipo === 'todos'
                  ? 'bg-[#f59e0b] border-[#f59e0b] text-white'
                  : 'border-gray-200 text-gray-600 hover:border-[#f59e0b]'
              }`}
            >
              Todos os tipos
            </button>
            {tipos.map((t) => (
              <button
                key={t}
                onClick={() => setFiltroTipo(t)}
                className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
                  filtroTipo === t
                    ? 'bg-[#f59e0b] border-[#f59e0b] text-white'
                    : 'border-gray-200 text-gray-600 hover:border-[#f59e0b]'
                }`}
              >
                {TIPO_LABELS[t] ?? t}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Lista */}
      <div className="space-y-2">
        {loading && filtradas.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
        ) : filtradas.length === 0 ? (
          <div className="text-center py-12 text-gray-400 text-sm">
            Nenhuma notificação encontrada
          </div>
        ) : (
          filtradas.map((n) => (
            <div
              key={n.id}
              className={`flex gap-4 p-4 rounded-xl border transition-colors ${
                !n.lida
                  ? 'bg-blue-50/50 border-blue-100'
                  : 'bg-white border-gray-100'
              }`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {TIPO_ICONS[n.tipo] ?? <Bell className="w-5 h-5 text-gray-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className={`text-sm text-gray-800 ${!n.lida ? 'font-semibold' : ''}`}>
                    {n.titulo}
                  </p>
                  {!n.lida && (
                    <span className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-500 mt-1.5" />
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-1">{n.mensagem}</p>
                {n.link && (
                  <a
                    href={n.link}
                    className="inline-block mt-1.5 text-xs text-[#1e3a8a] hover:text-[#f59e0b] transition-colors"
                  >
                    Ver detalhes →
                  </a>
                )}
                <p className="text-xs text-gray-400 mt-2">{tempoRelativo(n.created_at)}</p>
              </div>
              <div className="flex flex-col gap-1 flex-shrink-0">
                {!n.lida && (
                  <button
                    onClick={() => handleMarcarLida(n.id)}
                    className="p-1.5 rounded-lg hover:bg-blue-100 text-blue-500 transition-colors"
                    title="Marcar como lida"
                  >
                    <CheckCheck className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => handleRemover(n.id)}
                  className="p-1.5 rounded-lg hover:bg-red-100 text-gray-400 hover:text-red-500 transition-colors"
                  title="Remover"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Carregar mais */}
      {hasMore && filtradas.length > 0 && (
        <div className="mt-4 text-center">
          <button
            onClick={() => {
              setPage((p) => p + 1);
              carregar(false);
            }}
            disabled={loading}
            className="px-6 py-2 text-sm text-[#1e3a8a] border border-[#1e3a8a] rounded-lg hover:bg-blue-50 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Carregando...' : 'Carregar mais'}
          </button>
        </div>
      )}
    </div>
  );
}
