import { apiClient as api } from './client';

export type Perfil = 'admin' | 'operador' | 'visualizador';

export interface Permissao {
  perfil: Perfil;
  contextos_ids: number[];
  clientes_ids: number[];
}

export const permissoesApi = {
  get: async (usuarioId: number): Promise<Permissao> => {
    const { data } = await api.get<Permissao>(`/usuarios/${usuarioId}/permissoes`);
    return data;
  },

  set: async (usuarioId: number, dados: Permissao): Promise<Permissao> => {
    const { data } = await api.put<Permissao>(`/usuarios/${usuarioId}/permissoes`, dados);
    return data;
  },
};
