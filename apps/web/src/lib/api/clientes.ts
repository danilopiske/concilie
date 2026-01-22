import { apiClient } from './client';

export interface Cliente {
  cliente_id: number;
  nome_fantasia: string;
  razao_social: string;
  cnpj: string;
}

export const clientesApi = {
  listar: async (): Promise<Cliente[]> => {
    const { data } = await apiClient.get<Cliente[]>('/clientes/');
    return data;
  },

  listarEcs: async (clienteId: number): Promise<string[]> => {
    const { data } = await apiClient.get<string[]>(`/clientes/${clienteId}/ecs`);
    return data;
  },
};
