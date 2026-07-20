import { apiClient } from './client';

export interface ComparativoItem {
  bandeira: string;
  modalidade: string;
  taxa_contratada: number;
  taxa_media_cobrada: number;
  diferenca: number;
  status: 'ok' | 'divergente' | 'critico';
  quantidade_transacoes: number;
}

export interface ComparativoResponse {
  cliente_id: number;
  itens: ComparativoItem[];
  total_critico: number;
  total_divergente: number;
  total_ok: number;
}

export const taxasComparativoApi = {
  listar: (clienteId: number): Promise<ComparativoResponse> =>
    apiClient
      .get(`/clientes/${clienteId}/taxas-comparativo`)
      .then((r) => r.data),
};
