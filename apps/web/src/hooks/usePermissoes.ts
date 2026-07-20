'use client';

import { useEffect, useState } from 'react';
import { permissoesApi, type Perfil, type Permissao } from '@/lib/api/permissoes';

/** Permissões por módulo para cada perfil */
export const MODULO_PERMISSOES: Record<string, Perfil[]> = {
  dashboard:    ['admin', 'operador', 'visualizador'],
  importar:     ['admin', 'operador'],
  analise:      ['admin', 'operador', 'visualizador'],
  calculos:     ['admin', 'operador'],
  relatorios:   ['admin', 'operador', 'visualizador'],
  gestao:       ['admin'],
  configuracoes:['admin'],
};

/** Telas com acesso liberado individualmente por usuário (não por perfil) */
export const TELAS_POR_USUARIO = [
  'gestao', 'importar', 'analise', 'calculos', 'relatorios',
  'conversor', 'ia', 'configuracoes', 'dashboard',
] as const;

export function usePermissoes() {
  const [permissao, setPermissao] = useState<Permissao | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('user') : null;
    if (!stored) { setLoading(false); return; }

    const user = JSON.parse(stored) as { id: number };
    permissoesApi.get(user.id)
      .then(setPermissao)
      .catch((err) => {
        console.error('[usePermissoes] erro ao buscar permissoes:', err?.response?.status, err?.message);
        setPermissao({ perfil: 'visualizador', contextos_ids: [], clientes_ids: [], telas_permitidas: [] });
      })
      .finally(() => setLoading(false));
  }, []);

  const podeAcessar = (modulo: string): boolean => {
    if (!permissao) return false;
    const permitidos = MODULO_PERMISSOES[modulo] ?? ['admin'];
    return permitidos.includes(permissao.perfil);
  };

  const podeAcessarTela = (tela: string): boolean => {
    if (!permissao) return false;
    if (permissao.perfil === 'admin') return true;
    return (permissao.telas_permitidas ?? []).includes(tela);
  };

  return { permissao, loading, podeAcessar, podeAcessarTela };
}
