import { apiClient } from './client';

export interface ImportTaskItem {
  id: string;
  status: string;
  progress?: number;
  tipo_arquivo?: string;
  contexto?: string;
  usuario?: string;
  created_at: string;
}

export interface CalculoTaskItem {
  id: string;
  status: string;
  progress?: number;
  processamento_id?: string;
  tipo_taxa?: string;
  usuario?: string;
  created_at: string;
}

export interface RelatorioTaskItem {
  id: string;
  status: string;
  progress?: number;
  processamento_id?: string;
  tipo_relatorio?: string;
  usuario?: string;
  created_at: string;
}

export interface ClienteResumo {
  cliente_id: number;
  nome: string;
  cnpj?: string;
  notificacoes_nao_lidas: number;
  import_tasks_recentes: ImportTaskItem[];
  calculo_tasks_recentes: CalculoTaskItem[];
  relatorio_tasks_recentes: RelatorioTaskItem[];
}

export const clienteResumoApi = {
  getResumo: async (clienteId: number): Promise<ClienteResumo> => {
    const response = await apiClient.get<ClienteResumo>(`/clientes/${clienteId}/resumo`);
    return response.data;
  },
};
