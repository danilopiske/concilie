import { apiClient as api } from './client';

export interface Usuario {
  id: number;
  usuario: string;
  nome: string | null;
  empresa: string | null;
}

export interface UsuarioCreate {
  usuario: string;
  senha: string;
  nome?: string;
  empresa?: string;
}

export interface UsuarioUpdate {
  usuario?: string;
  senha?: string;
  nome?: string;
  empresa?: string;
}

export const usuariosApi = {
  listar: async () => {
    const { data } = await api.get<Usuario[]>('/usuarios/');
    return data;
  },

  criar: async (dados: UsuarioCreate) => {
    const { data } = await api.post<Usuario>('/usuarios/', dados);
    return data;
  },

  atualizar: async (id: number, dados: UsuarioUpdate) => {
    const { data } = await api.put<Usuario>(`/usuarios/${id}`, dados);
    return data;
  },

  deletar: async (id: number) => {
    await api.delete(`/usuarios/${id}`);
  },

  getPermissoes: async (id: number) => {
    const { data } = await api.get(`/usuarios/${id}/permissoes`);
    return data as { perfil: string; contextos_ids: number[]; clientes_ids: number[] };
  },

  setPermissoes: async (id: number, dados: { perfil: string; contextos_ids: number[]; clientes_ids: number[] }) => {
    const { data } = await api.put(`/usuarios/${id}/permissoes`, dados);
    return data;
  },
};
