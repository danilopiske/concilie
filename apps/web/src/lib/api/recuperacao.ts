import { apiClient } from './client';

export interface RankingItem {
  posicao: number;
  cliente_id: number | string;
  nome: string;
  total_perda_rs: number;
  count_transacoes: number;
  media_perda_rs: number;
}

export interface RankingRecuperacao {
  total_clientes_com_perda: number;
  total_recuperavel_rs: number;
  ranking: RankingItem[];
}

export const recuperacaoApi = {
  getRanking: async (limit = 20): Promise<RankingRecuperacao> => {
    const r = await apiClient.get<RankingRecuperacao>('/recuperacao/ranking', {
      params: { limit },
    });
    return r.data;
  },
  exportarCsvUrl: () =>
    `${apiClient.defaults.baseURL}/recuperacao/ranking/exportar-csv`,
};
