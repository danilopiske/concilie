import { apiClient } from './client';

export interface Divergencia {
  bandeira: string;
  modalidade: string;
  taxa_contratada: number;
  taxa_cobrada: number;
  diferenca_pct: number;
  status: string;
}

export interface DivergenciasRelatorio {
  cliente_id: number;
  nome: string;
  total_divergencias: number;
  nota: string | null;
  divergencias: Divergencia[];
}

export interface DivergenciaConsolidadaItem {
  cliente_id: number;
  nome_cliente: string;
  total_divergencias: number;
  valor_total_divergente: number;
  ultima_divergencia: string | null;
}

export interface DivergenciasConsolidado {
  items: DivergenciaConsolidadaItem[];
  total: number;
}

export const divergenciasApi = {
  getRelatorio: async (clienteId: number): Promise<DivergenciasRelatorio> => {
    const r = await apiClient.get<DivergenciasRelatorio>(`/divergencias/${clienteId}`);
    return r.data;
  },
  exportarCsvUrl: (clienteId: number): string => {
    return `${apiClient.defaults.baseURL}/divergencias/${clienteId}/exportar-csv`;
  },
  getConsolidado: async (limit = 20, offset = 0): Promise<DivergenciasConsolidado> => {
    const r = await apiClient.get<DivergenciasConsolidado>('/divergencias', {
      params: { limit, offset },
    });
    return r.data;
  },
};
