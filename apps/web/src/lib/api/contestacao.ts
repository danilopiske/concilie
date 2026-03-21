import { apiClient } from './client';

export type ContestacaoStatus = 'rascunho' | 'enviada' | 'em_analise' | 'deferida' | 'indeferida';

export interface ContestacaoResumoItem {
  id: string;
  status: ContestacaoStatus | string;
  adquirente: string;
  processamento_id: number | null;
  periodo_inicio: string | null;
  periodo_fim: string | null;
  valor_excesso_total: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ContestacoesPorCliente {
  cliente_id: number;
  nome: string;
  total: number;
  contestacoes: ContestacaoResumoItem[];
}

export interface ContestacaoResponse {
  id: string;
  cliente_id: number;
  processamento_id: number | null;
  adquirente: string;
  periodo_inicio: string;
  periodo_fim: string;
  valor_excesso_total: number;
  status: ContestacaoStatus;
  html_carta: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export const contestacaoApi = {
  gerar: (cliente_id: number, processamento_id: number): Promise<{ contestacao_id: string }> =>
    apiClient.post('/contestacoes/gerar', { cliente_id, processamento_id }).then((r) => r.data),

  listar: (cliente_id?: number, status?: string): Promise<ContestacaoResponse[]> =>
    apiClient
      .get('/contestacoes', {
        params: {
          ...(cliente_id !== undefined ? { cliente_id } : {}),
          ...(status ? { status } : {}),
        },
      })
      .then((r) => r.data),

  obter: (id: string): Promise<ContestacaoResponse> =>
    apiClient.get(`/contestacoes/${id}`).then((r) => r.data),

  atualizarStatus: (id: string, status: ContestacaoStatus): Promise<ContestacaoResponse> =>
    apiClient.put(`/contestacoes/${id}/status`, { status }).then((r) => r.data),

  saveEdit: (id: string, html_content: string): Promise<{ saved: boolean }> =>
    apiClient.post(`/contestacoes/${id}/save-edit`, { html_content }).then((r) => r.data),

  downloadUrl: (id: string): string =>
    `${apiClient.defaults.baseURL}/contestacoes/${id}/download`,

  remover: (id: string): Promise<void> =>
    apiClient.delete(`/contestacoes/${id}`).then(() => undefined),

  porCliente: (clienteId: number): Promise<ContestacoesPorCliente> =>
    apiClient.get<ContestacoesPorCliente>(`/contestacoes/cliente/${clienteId}`).then((r) => r.data),
};
