import { apiClient } from './client';

export interface ExtratoCliente {
  id: string;
  cliente_id: number;
  nome_arquivo: string;
  tipo: string;
  uploaded_by: string | null;
  uploaded_at: string;
  status: 'aguardando' | 'importado' | 'divergente';
  processamento_id: number | null;
}

export interface ExtratoStatusResumo {
  total: number;
  aguardando: number;
  importado: number;
  divergente: number;
}

export const extratoClienteApi = {
  listar: async (clienteId: number): Promise<ExtratoCliente[]> => {
    const r = await apiClient.get<ExtratoCliente[]>(`clientes/${clienteId}/extratos`);
    return r.data;
  },

  upload: async (clienteId: number, file: File, tipo: string): Promise<ExtratoCliente> => {
    const form = new FormData();
    form.append('file', file);
    form.append('tipo', tipo);
    const r = await apiClient.post<ExtratoCliente>(`clientes/${clienteId}/extratos`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return r.data;
  },

  validar: async (clienteId: number): Promise<{ atualizados: number; total_pendentes: number }> => {
    const r = await apiClient.post(`clientes/${clienteId}/extratos/validar`);
    return r.data;
  },

  statusResumo: async (clienteId: number): Promise<ExtratoStatusResumo> => {
    const r = await apiClient.get<ExtratoStatusResumo>(`clientes/${clienteId}/extratos/status-resumo`);
    return r.data;
  },

  downloadUrl: (clienteId: number, extratoId: string): string => {
    const base = apiClient.defaults.baseURL ?? '';
    return `${base}/clientes/${clienteId}/extratos/${extratoId}/download`;
  },

  deletar: async (clienteId: number, extratoId: string): Promise<void> => {
    await apiClient.delete(`clientes/${clienteId}/extratos/${extratoId}`);
  },
};
