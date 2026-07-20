'use client';
import { useEffect, useState } from 'react';
import { Shield, User, Key, LogIn } from 'lucide-react';
import { auditoriaApi, type AuditLogItem } from '@/lib/api/auditoria';

const ACAO_CONFIG: Record<string, { label: string; icon: React.ReactNode; cor: string }> = {
  login: { label: 'Login', icon: <LogIn className="w-4 h-4" />, cor: 'text-blue-600 bg-blue-50' },
  alterar_senha: { label: 'Senha Alterada', icon: <Key className="w-4 h-4" />, cor: 'text-amber-600 bg-amber-50' },
};

function formatarData(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AuditoriaPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    auditoriaApi
      .listar({ limit: 50 })
      .then(setLogs)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Shield className="w-6 h-6 text-[#1e3a8a]" />
        <div>
          <h1 className="text-xl font-bold text-gray-900">Log de Auditoria</h1>
          <p className="text-sm text-gray-500">Histórico de ações realizadas na sua conta</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400 text-sm">Carregando...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-12 text-gray-400 text-sm">Nenhuma ação registrada.</div>
      ) : (
        <div className="space-y-2">
          {logs.map((log) => {
            const config = ACAO_CONFIG[log.acao];
            return (
              <div
                key={log.id}
                className="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-4"
              >
                <div className={`p-2 rounded-lg ${config?.cor ?? 'bg-gray-50 text-gray-600'}`}>
                  {config?.icon ?? <Shield className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-gray-800">
                      {config?.label ?? log.acao}
                    </p>
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {formatarData(log.created_at)}
                    </span>
                  </div>
                  {log.detalhes && (
                    <p className="text-xs text-gray-500 mt-0.5">{log.detalhes}</p>
                  )}
                  {log.usuario && (
                    <div className="flex items-center gap-1 mt-1">
                      <User className="w-3 h-3 text-gray-400" />
                      <span className="text-xs text-gray-400">{log.usuario}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
