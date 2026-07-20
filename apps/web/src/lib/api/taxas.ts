/**
 * API client para Taxas
 */
import { apiClient } from './client';

export interface Taxa {
  id: number;
  ec: string;
  bandeira: string | null;
  forma_pagamento: string;
  parcelado: 'S' | 'N';
  parcelas_ini: number;
  parcelas_fim: number;
  data_ini: string;
  data_fim: string | null;
  taxa: number;
  contexto: string;
}

export interface TaxaCreate {
  ec: string;
  bandeira?: string | null;
  forma_pagamento: string;
  parcelado: 'S' | 'N';
  parcelas_ini: number;
  parcelas_fim: number;
  data_ini: string;
  data_fim?: string | null;
  taxa: number;
  contexto?: string;
}

export interface TaxaCopiarRequest {
  ec_origem: string;
  ecs_destino: string[];
  sobrescrever: boolean;
  contexto?: string;
}

export interface TaxaCopiarResponse {
  copiadas: number;
  removidas: number;
  erros: string[];
}

export const taxasApi = {
  async listarPorEC(ec: string, contexto: string = 'padrao'): Promise<Taxa[]> {
    const { data } = await apiClient.get<Taxa[]>(`/taxas/${ec}`, {
      params: { contexto }
    });
    return data;
  },

  async criar(taxa: TaxaCreate): Promise<{ message: string; taxa: Taxa }> {
    const { data } = await apiClient.post('/taxas/', taxa);
    return data;
  },

  async atualizar(taxaId: number, taxa: Partial<TaxaCreate>): Promise<{ message: string }> {
    const { data } = await apiClient.put(`/taxas/${taxaId}`, taxa);
    return data;
  },

  async deletar(taxaId: number): Promise<{ message: string }> {
    const { data } = await apiClient.delete(`/taxas/${taxaId}`);
    return data;
  },

  async copiar(request: TaxaCopiarRequest): Promise<TaxaCopiarResponse> {
    const { data } = await apiClient.post<TaxaCopiarResponse>('/taxas/copiar', request);
    return data;
  },
};
