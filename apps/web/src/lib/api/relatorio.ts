import { apiClient } from './client';

export interface RelatorioOptions {
  processamentos: Array<{id: string, label: string}>;
  adquirentes: string[];
}

export interface RelatorioRequest {
  processamento_id: string;
  calc_tipo?: string;
  tipo_relatorio: 'mensal' | 'retroativo';
  
  // Filtros
  data_inicio?: string; // YYYY-MM-DD
  data_fim?: string;   // YYYY-MM-DD
  adquirente?: string;
  
  // Opções
  incluir_filtradas: boolean;
  incluir_recebiveis_filtrados: boolean;
  apenas_com_perdas: boolean;
  modelo?: 'completo' | 'sem_capa';
}

export interface RelatorioResponse {
  success: boolean;
  message: string;
  html_path?: string;
  excel_path?: string;
  sintetico_path?: string;
  abusividade_path?: string;
  filename?: string;
}

export interface RelatorioTask {
  id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';
  progress: number;
  message: string;
  tipo_relatorio: string;
  result_path?: string;
  abusividade_path?: string;
  sintetico_path?: string;
  excel_path?: string;
  processamento_id?: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}

export const relatorioApi = {
  getHistorico: async (processamentoId?: string, skip: number = 0, limit: number = 50, status?: string, tipo?: string): Promise<RelatorioTask[]> => {
    const params: Record<string, unknown> = { skip, limit };
    if (processamentoId) params.processamento_id = processamentoId;
    if (status) params.status = status;
    if (tipo) params.tipo = tipo;
    const response = await apiClient.get<RelatorioTask[]>('/relatorios/historico', { params });
    return response.data;
  },

  getOpcoes: async (processamentoId?: string): Promise<RelatorioOptions> => {
    const params = processamentoId ? { processamento_id: processamentoId } : undefined;
    const response = await apiClient.get<RelatorioOptions>('/relatorios/opcoes', { params });
    return response.data;
  },

  getAdquirentes: async (processamentoId: string, calcTipo?: string): Promise<{
    adquirentes: string[], 
    periodo: {data_min: string, data_max: string} | null,
    available_types: string[]
  }> => {
    const response = await apiClient.get<{
      adquirentes: string[], 
      periodo: {data_min: string, data_max: string} | null,
      available_types: string[]
    }>('/relatorios/adquirentes', { 
      params: { 
        processamento_id: processamentoId,
        calc_tipo: calcTipo
      } 
    });
    return response.data;
  },

  gerar: async (req: RelatorioRequest): Promise<RelatorioResponse> => {
    const response = await apiClient.post<RelatorioResponse>('/relatorios/gerar', req, {
        timeout: 300000 
    });
    return response.data;
  },

  gerarAsync: async (req: RelatorioRequest): Promise<{task_id: string}> => {
    const response = await apiClient.post<{task_id: string}>('/relatorios/gerar-async', req);
    return response.data;
  },

  getTaskStatus: async (taskId: string): Promise<RelatorioTask> => {
    const response = await apiClient.get<RelatorioTask>(`/relatorios/task/${taskId}`);
    return response.data;
  },

  downloadUrl: (path: string) => {
    const baseUrl = apiClient.defaults.baseURL;
    return `${baseUrl}/relatorios/download?path=${encodeURIComponent(path)}`;
  },

  taskDownloadUrl: (taskId: string, format: 'html' | 'pdf' = 'html') => {
    const baseUrl = apiClient.defaults.baseURL;
    return `${baseUrl}/relatorios/tasks/${taskId}/download?format=${format}`;
  },

  saveEdit: async (taskId: string, htmlContent: string): Promise<{ success: boolean; path: string }> => {
    const response = await apiClient.post<{ success: boolean; path: string }>(
      `/relatorios/tasks/${taskId}/save-edit`,
      { html_content: htmlContent }
    );
    return response.data;
  },
};
