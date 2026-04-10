import { apiClient } from './client';

export interface Notificacao {
  id: string;
  usuario_id: number | null;
  tipo: string;
  titulo: string;
  mensagem: string;
  link: string | null;
  lida: boolean;
  created_at: string;
}

export interface NotificacaoCount {
  count: number;
}

export const notificacaoApi = {
  listar: async (params?: {
    lida?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<Notificacao[]> => {
    const response = await apiClient.get<Notificacao[]>('/notificacoes', { params });
    return response.data;
  },

  contarNaoLidas: async (): Promise<NotificacaoCount> => {
    const response = await apiClient.get<NotificacaoCount>('/notificacoes/nao-lidas/count');
    return response.data;
  },

  marcarLida: async (id: string): Promise<Notificacao> => {
    const response = await apiClient.put<Notificacao>(`/notificacoes/${id}/lida`);
    return response.data;
  },

  marcarTodasLidas: async (): Promise<void> => {
    await apiClient.put('/notificacoes/marcar-todas-lidas');
  },

  remover: async (id: string): Promise<void> => {
    await apiClient.delete(`/notificacoes/${id}`);
  },
};
