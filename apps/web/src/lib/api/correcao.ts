import { apiClient as api } from './client';
import type { ResumoResponse, AtualizarRequest, RemoverRequest, HistoricoItem } from '../types/correcao';

export const correcaoService = {
  obterResumo: async (processamentoId: string): Promise<ResumoResponse> => {
    const { data } = await api.get<ResumoResponse>('/correcao/resumo', { params: { processamento_id: processamentoId } });
    return data;
  },

  atualizarEmMassa: async (req: AtualizarRequest): Promise<{ linhas_afetadas: number }> => {
    const { data } = await api.patch<{ linhas_afetadas: number }>('/correcao/atualizar', req);
    return data;
  },

  removerEmMassa: async (req: RemoverRequest): Promise<{ linhas_afetadas: number }> => {
    const { data } = await api.post<{ linhas_afetadas: number }>('/correcao/remover', req);
    return data;
  },

  obterHistorico: async (processamentoId: string): Promise<HistoricoItem[]> => {
    const { data } = await api.get<HistoricoItem[]>('/correcao/historico', { params: { processamento_id: processamentoId } });
    return data;
  }
};
