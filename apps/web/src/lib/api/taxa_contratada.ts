import { apiClient } from './client';

export interface TaxaContratadaCreate {
  bandeira: string;
  modalidade: string;
  taxa_contratada: number;
  vigencia_inicio: string; // ISO date
  vigencia_fim?: string | null;
  observacao?: string | null;
}

export interface TaxaContratadaResponse {
  id: number;
  cliente_id: number;
  bandeira: string;
  modalidade: string;
  taxa_contratada: number;
  vigencia_inicio: string;
  vigencia_fim: string | null;
  observacao: string | null;
  created_at: string;
}

export interface DesvioTaxa {
  bandeira: string;
  modalidade: string;
  taxa_contratada: number;
  taxa_media_cobrada: number;
  desvio_percentual: number;
  valor_total_transacoes: number;
  valor_excesso_estimado: number;
  status: 'ok' | 'atencao' | 'abusivo';
  quantidade_transacoes: number;
}

export interface ComparacaoResponse {
  cliente_id: number;
  processamento_id: string;
  desvios: DesvioTaxa[];
  valor_excesso_total: number;
}

export const taxaContratadaApi = {
  listar: (clienteId: number, vigente?: boolean): Promise<TaxaContratadaResponse[]> =>
    apiClient
      .get(`/clientes/${clienteId}/taxas-contratadas`, { params: vigente !== undefined ? { vigente } : {} })
      .then((r) => r.data),

  criar: (clienteId: number, data: TaxaContratadaCreate): Promise<TaxaContratadaResponse> =>
    apiClient.post(`/clientes/${clienteId}/taxas-contratadas`, data).then((r) => r.data),

  atualizar: (clienteId: number, id: number, data: Partial<TaxaContratadaCreate>): Promise<TaxaContratadaResponse> =>
    apiClient.put(`/clientes/${clienteId}/taxas-contratadas/${id}`, data).then((r) => r.data),

  remover: (clienteId: number, id: number): Promise<void> =>
    apiClient.delete(`/clientes/${clienteId}/taxas-contratadas/${id}`).then(() => undefined),

  comparacao: (clienteId: number, processamentoId: string): Promise<ComparacaoResponse> =>
    apiClient
      .get(`/clientes/${clienteId}/taxas-contratadas/comparacao`, { params: { processamento_id: processamentoId } })
      .then((r) => r.data),
};
