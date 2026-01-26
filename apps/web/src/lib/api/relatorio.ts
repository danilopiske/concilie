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
}

export interface RelatorioResponse {
  success: boolean;
  message: string;
  html_path?: string;
  excel_path?: string;
  sintetico_path?: string;
  filename?: string;
}

export const relatorioApi = {
  getOpcoes: async (processamentoId?: string): Promise<RelatorioOptions> => {
    const params = processamentoId ? { processamento_id: processamentoId } : undefined;
    const response = await apiClient.get<RelatorioOptions>('/relatorios/opcoes', { params });
    return response.data;
  },

  getAdquirentes: async (processamentoId: string): Promise<string[]> => {
    // Using query param to safely handle special chars in ID
    const response = await apiClient.get<string[]>('/relatorios/adquirentes', { 
      params: { processamento_id: processamentoId } 
    });
    return response.data;
  },

  gerar: async (req: RelatorioRequest): Promise<RelatorioResponse> => {
    // Reports can take long, override default 30s timeout to 5min
    const response = await apiClient.post<RelatorioResponse>('/relatorios/gerar', req, {
        timeout: 300000 
    });
    return response.data;
  },

  downloadUrl: (path: string) => {
    // Construct absolute URL for download if needed, or use a proxy endpoint
    // Assuming backend is at same host/port for now or standard base URL
    // Actually we need to call the download endpoint
    return `${apiClient.defaults.baseURL}/relatorios/download?path=${encodeURIComponent(path)}`;
  }
};
