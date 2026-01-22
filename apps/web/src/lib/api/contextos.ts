import { apiClient } from './client';

export interface Contexto {
  id: number;
  nome: string;
  descricao?: string;
  ativo: boolean;
}

export const contextosApi = {
  listar: async (): Promise<Contexto[]> => {
    const { data } = await apiClient.get<Contexto[]>('/contextos/');
    return data;
  },
};
