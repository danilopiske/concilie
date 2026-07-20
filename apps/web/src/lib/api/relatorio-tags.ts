import { apiClient } from './client';

export interface RelatorioTag {
  id: number;
  nome: string;
  tipo: 'secao' | 'clausula' | 'assinatura' | 'cabecalho' | 'rodape';
  descricao?: string;
  conteudo_padrao: string;
  ativo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RelatorioTagCreate {
  nome: string;
  tipo: RelatorioTag['tipo'];
  descricao?: string;
  conteudo_padrao: string;
  ativo?: boolean;
}

export interface RelatorioTagUpdate {
  nome?: string;
  tipo?: RelatorioTag['tipo'];
  descricao?: string;
  conteudo_padrao?: string;
  ativo?: boolean;
}

export const relatorioTagsApi = {
  listar: async (ativo: 'true' | 'false' | 'all' = 'true'): Promise<RelatorioTag[]> => {
    const response = await apiClient.get<RelatorioTag[]>('/relatorio-tags/', { params: { ativo } });
    return response.data;
  },

  criar: async (data: RelatorioTagCreate): Promise<RelatorioTag> => {
    const response = await apiClient.post<RelatorioTag>('/relatorio-tags/', data);
    return response.data;
  },

  obter: async (tagId: number): Promise<RelatorioTag> => {
    const response = await apiClient.get<RelatorioTag>(`/relatorio-tags/${tagId}`);
    return response.data;
  },

  atualizar: async (tagId: number, data: RelatorioTagUpdate): Promise<RelatorioTag> => {
    const response = await apiClient.put<RelatorioTag>(`/relatorio-tags/${tagId}`, data);
    return response.data;
  },

  excluir: async (tagId: number): Promise<void> => {
    await apiClient.delete(`/relatorio-tags/${tagId}`);
  },
};
