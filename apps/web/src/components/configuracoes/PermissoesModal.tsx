'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { usuariosApi } from '@/lib/api/usuarios';
import type { Usuario } from '@/lib/api/usuarios';
import { TELAS_POR_USUARIO } from '@/hooks/usePermissoes';

type Perfil = 'admin' | 'operador' | 'visualizador';

const TELA_LABELS: Record<string, string> = {
  gestao:       'Gestão',
  importar:     'Importar',
  analise:      'Análise e Correções',
  calculos:     'Cálculos',
  relatorios:   'Relatórios',
  conversor:    'Conversor (Rede)',
  ia:           'Assistente IA',
  configuracoes:'Configurações',
  dashboard:    'Notificações / Tarefas',
};

interface PermissoesModalProps {
  isOpen: boolean;
  onClose: () => void;
  usuario: Usuario | null;
}

export function PermissoesModal({ isOpen, onClose, usuario }: PermissoesModalProps) {
  const [perfil, setPerfil] = useState<Perfil>('operador');
  const [contextosIds, setContextosIds] = useState<number[]>([]);
  const [clientesIds, setClientesIds] = useState<number[]>([]);
  const [telasPermitidas, setTelasPermitidas] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !usuario) return;
    setLoading(true);
    setError(null);
    usuariosApi.getPermissoes(usuario.id)
      .then((p) => {
        setPerfil(p.perfil as Perfil);
        setContextosIds(p.contextos_ids);
        setClientesIds(p.clientes_ids);
        setTelasPermitidas(p.telas_permitidas ?? []);
      })
      .catch(() => setError('Não foi possível carregar as permissões.'))
      .finally(() => setLoading(false));
  }, [isOpen, usuario]);

  const handleSave = async () => {
    if (!usuario) return;
    setSaving(true);
    setError(null);
    try {
      await usuariosApi.setPermissoes(usuario.id, {
        perfil,
        contextos_ids: contextosIds,
        clientes_ids: clientesIds,
        telas_permitidas: telasPermitidas,
      });
      onClose();
    } catch {
      setError('Erro ao salvar permissões. Tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen || !usuario) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-5">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Permissões — {usuario.nome ?? usuario.usuario}</h2>
          <p className="text-sm text-gray-500">Configure perfil e escopos de acesso</p>
        </div>

        {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">{error}</p>}

        {loading ? (
          <div className="flex justify-center py-6">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Perfil */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Perfil de acesso</label>
              <select
                value={perfil}
                onChange={(e) => setPerfil(e.target.value as Perfil)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="admin">Admin — acesso total</option>
                <option value="operador">Operador — importação, análise, cálculos</option>
                <option value="visualizador">Visualizador — somente leitura</option>
              </select>
            </div>

            {/* Contextos */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contextos permitidos
                <span className="ml-1 text-xs text-gray-400">(vazio = todos)</span>
              </label>
              <input
                type="text"
                placeholder="IDs separados por vírgula, ex: 1,2,3"
                value={contextosIds.join(', ')}
                onChange={(e) => {
                  const ids = e.target.value.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
                  setContextosIds(ids);
                }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Clientes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Clientes permitidos
                <span className="ml-1 text-xs text-gray-400">(vazio = todos)</span>
              </label>
              <input
                type="text"
                placeholder="IDs separados por vírgula, ex: 10,20"
                value={clientesIds.join(', ')}
                onChange={(e) => {
                  const ids = e.target.value.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
                  setClientesIds(ids);
                }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            {/* Telas especiais por usuário */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Módulos especiais
                <span className="ml-1 text-xs text-gray-400">(liberados individualmente, admin sempre tem acesso)</span>
              </label>
              <div className="space-y-2">
                {TELAS_POR_USUARIO.map((tela) => {
                  const ativo = telasPermitidas.includes(tela);
                  return (
                    <label key={tela} className="flex items-center gap-3 cursor-pointer">
                      <div
                        onClick={() =>
                          setTelasPermitidas(ativo
                            ? telasPermitidas.filter(t => t !== tela)
                            : [...telasPermitidas, tela])
                        }
                        className={`relative w-10 h-5 rounded-full transition-colors ${ativo ? 'bg-primary-600' : 'bg-gray-300'}`}
                      >
                        <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${ativo ? 'translate-x-5' : ''}`} />
                      </div>
                      <span className="text-sm text-gray-700">{TELA_LABELS[tela] ?? tela}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onClose} disabled={saving}>Cancelar</Button>
          <Button onClick={handleSave} disabled={loading || saving}>
            {saving ? 'Salvando...' : 'Salvar permissões'}
          </Button>
        </div>
      </div>
    </div>
  );
}
