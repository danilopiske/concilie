import { apiClient } from './client';
import { DeParaRule, DeParaCreate } from '@/lib/types/importacao';

export const deparaApi = {
  listar: async (params?: { 
    cliente_id?: number; 
    contexto?: string; 
    tipo_origem?: string; 
    ativo?: number; 
    search?: string; 
  }): Promise<DeParaRule[]> => {
    const { data } = await apiClient.get<DeParaRule[]>('/depara/', { params });
    return data;
  },

  criar: async (depara: DeParaCreate): Promise<DeParaRule> => {
    const { data } = await apiClient.post<DeParaRule>('/depara/', depara);
    return data;
  },

  atualizar: async (id: number, depara: Partial<DeParaCreate>): Promise<DeParaRule> => {
    const { data } = await apiClient.put<DeParaRule>(`/depara/${id}`, depara);
    return data;
  },

  deletar: async (id: number): Promise<void> => {
    await apiClient.delete(`/depara/${id}`);
  },

  lerCabecalhos: async (file: File): Promise<{ headers: string[], debug_info?: unknown }> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await apiClient.post<{ headers: string[], debug_info?: unknown }>('/depara/ler-cabecalhos', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  },

  listarColunasSistema: async (tipo: string): Promise<string[]> => {
    const { data } = await apiClient.get<string[]>('/depara/colunas-sistema', {
      params: { tipo }
    });
    return data;
  },
};
