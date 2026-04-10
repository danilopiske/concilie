'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { Bell, Check, CheckCheck, Trash2 } from 'lucide-react';
import { type Notificacao, notificacaoApi } from '@/lib/api/notificacao';

const ICONS_BY_TIPO: Record<string, string> = {
  relatorio_ok: '📊',
  relatorio_erro: '❌',
  abusividade_detectada: '⚠️',
  importacao_ok: '✅',
  importacao_erro: '❌',
};

function tempoRelativo(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'agora';
  if (mins < 60) return `${mins}min atrás`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h atrás`;
  const days = Math.floor(hrs / 24);
  return `${days}d atrás`;
}

export function NotificacaoBell() {
  const [count, setCount] = useState(0);
  const [notificacoes, setNotificacoes] = useState<Notificacao[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const fetchCount = async () => {
    try {
      const data = await notificacaoApi.contarNaoLidas();
      setCount(data.count);
    } catch {
      // silencioso
    }
  };

  const fetchNotificacoes = async () => {
    try {
      const data = await notificacaoApi.listar({ limit: 5 });
      setNotificacoes(data);
    } catch {
      // silencioso
    }
  };

  // Polling a cada 30s
  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fechar ao clicar fora
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleOpen = () => {
    if (!open) fetchNotificacoes();
    setOpen((v) => !v);
  };

  const handleMarcarLida = async (id: string) => {
    await notificacaoApi.marcarLida(id);
    setNotificacoes((prev) =>
      prev.map((n) => (n.id === id ? { ...n, lida: true } : n))
    );
    setCount((c) => Math.max(0, c - 1));
  };

  const handleRemover = async (id: string, lida: boolean) => {
    await notificacaoApi.remover(id);
    setNotificacoes((prev) => prev.filter((n) => n.id !== id));
    if (!lida) setCount((c) => Math.max(0, c - 1));
  };

  const handleMarcarTodas = async () => {
    await notificacaoApi.marcarTodasLidas();
    setNotificacoes((prev) => prev.map((n) => ({ ...n, lida: true })));
    setCount(0);
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={handleOpen}
        className="relative p-2 rounded-full hover:bg-white/10 transition-colors"
        aria-label="Notificações"
      >
        <Bell className="w-5 h-5 text-white" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full px-0.5">
            {count > 99 ? '99+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <span className="text-sm font-semibold text-gray-800">Notificações</span>
            {count > 0 && (
              <button
                onClick={handleMarcarTodas}
                className="flex items-center gap-1 text-xs text-[#1e3a8a] hover:text-[#f59e0b] transition-colors"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Marcar todas como lidas
              </button>
            )}
          </div>

          {/* Lista */}
          <div className="max-h-72 overflow-y-auto divide-y divide-gray-50">
            {notificacoes.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-400">
                Nenhuma notificação
              </div>
            ) : (
              notificacoes.map((n) => (
                <div
                  key={n.id}
                  className={`flex gap-3 px-4 py-3 hover:bg-gray-50 transition-colors ${
                    !n.lida ? 'bg-blue-50/40' : ''
                  }`}
                >
                  <span className="text-lg flex-shrink-0 mt-0.5">
                    {ICONS_BY_TIPO[n.tipo] ?? '🔔'}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-medium text-gray-800 truncate ${!n.lida ? 'font-semibold' : ''}`}>
                      {n.titulo}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.mensagem}</p>
                    <p className="text-[10px] text-gray-400 mt-1">{tempoRelativo(n.created_at)}</p>
                  </div>
                  <div className="flex flex-col gap-1 flex-shrink-0">
                    {!n.lida && (
                      <button
                        onClick={() => handleMarcarLida(n.id)}
                        className="p-1 rounded hover:bg-blue-100 text-blue-500 transition-colors"
                        title="Marcar como lida"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <button
                      onClick={() => handleRemover(n.id, n.lida)}
                      className="p-1 rounded hover:bg-red-100 text-gray-400 hover:text-red-500 transition-colors"
                      title="Remover"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-100 px-4 py-2.5">
            <Link
              href="/notificacoes"
              onClick={() => setOpen(false)}
              className="block text-center text-xs text-[#1e3a8a] hover:text-[#f59e0b] font-medium transition-colors"
            >
              Ver todas as notificações →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
