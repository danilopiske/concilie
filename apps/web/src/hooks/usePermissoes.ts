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

export function usePermissoes() {
  const [permissao, setPermissao] = useState<Permissao | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('user') : null;
    if (!stored) { setLoading(false); return; }

    const user = JSON.parse(stored) as { id: number };
    permissoesApi.get(user.id)
      .then(setPermissao)
      .catch(() => {
        // fallback: admin para não bloquear usuários sem permissão cadastrada
        setPermissao({ perfil: 'admin', contextos_ids: [], clientes_ids: [] });
      })
      .finally(() => setLoading(false));
  }, []);

  const podeAcessar = (modulo: string): boolean => {
    if (!permissao) return false;
    const permitidos = MODULO_PERMISSOES[modulo] ?? ['admin'];
    return permitidos.includes(permissao.perfil);
  };

  return { permissao, loading, podeAcessar };
}
