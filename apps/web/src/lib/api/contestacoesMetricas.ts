import { apiClient } from './client';

export interface ContestacaoTopCliente {
  cliente_id: number;
  nome: string;
  total_recuperado_rs: number;
  total_deferidas: number;
}

export interface ContestacaoMetricas {
  por_status: Record<string, number>;
  total_contestacoes: number;
  total_enviadas: number;
  total_deferidas: number;
  taxa_sucesso_pct: number;
  valor_recuperado_rs: number;
  valor_em_disputa_rs: number;
  top_clientes_recuperacao: ContestacaoTopCliente[];
}

export const contestacoesMetricasApi = {
  get: async (): Promise<ContestacaoMetricas> => {
    const r = await apiClient.get<ContestacaoMetricas>('/contestacoes-metricas');
    return r.data;
  },
};
