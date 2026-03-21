import { apiClient } from './client';

export interface AuditLogItem {
  id: string;
  usuario_id: number | null;
  usuario: string | null;
  acao: string;
  detalhes: string | null;
  ip: string | null;
  created_at: string;
}

export const auditoriaApi = {
  listar: async (params?: { skip?: number; limit?: number }): Promise<AuditLogItem[]> => {
    const response = await apiClient.get<AuditLogItem[]>('/auditoria', { params });
    return response.data;
  },
};
