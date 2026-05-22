import { apiClient } from './client';

export interface AgregacaoBase {
  quantidade: number;
  valor_total: number;
  valor_medio?: number;
  valor_min?: number;
  valor_max?: number;
}

export interface AgregacaoBandeira extends AgregacaoBase {
  bandeira: string;
  taxa_perc_media?: number;
  taxa_valor_total?: number;
  vl_rr_total?: number;
}

export interface AgregacaoFormaPagamento extends AgregacaoBase {
  forma_pagamento: string;
  taxa_perc_media?: number;
  taxa_valor_total?: number;
  vl_rr_total?: number;
}

export interface AgregacaoPeriodo extends AgregacaoBase {
  tipo_periodo: string;
  periodo: string;
}

export interface AgregacaoRecebivel {
  tipo_recebivel: string;
  quantidade: number;
  valor_total: number;
}

export interface AgregacaoBandeiraForma {
  bandeira: string;
  forma_pagamento: string;
  quantidade: number;
  valor_total: number;
  valor_medio?: number;
  taxa_perc_media?: number;
  taxa_valor_total?: number;
  vl_rr_total?: number;
}

export interface ConformidadeBandeiraForma {
  bandeira: string;
  forma_pagamento: string;
  quantidade: number;
  faturamento: number;
  cielo_liquido: number;
  cielo_taxa_media?: number;
  cielo_retido: number;
  calc_liquido: number;
  calc_taxa_media?: number;
  calc_retido: number;
  nao_conformidade: number;
  nao_conformidade_perc?: number;
  perda_rr?: number;
}

export interface AgregacaoFormaPagamentoAno {
  ano: string;
  forma_pagamento: string;
  quantidade: number;
  valor_total: number;
  valor_medio: number;
  taxa_perc_minima?: number;
  taxa_perc_maxima?: number;
}

export const analistaApi = {
  getBandeiras: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoBandeira[]>(`/analista/${processamentoId}/bandeiras`);
    return data;
  },

  getFormasPagamento: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoFormaPagamento[]>(`/analista/${processamentoId}/formas-pagamento`);
    return data;
  },

  getPeriodos: async (processamentoId: string, tipo: 'mes' | 'trimestre' | 'semestre' | 'ano') => {
    const { data } = await apiClient.get<AgregacaoPeriodo[]>(`/analista/${processamentoId}/periodos`, {
      params: { tipo }
    });
    return data;
  },

  getRecebiveis: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoRecebivel[]>(`/analista/${processamentoId}/recebiveis`);
    return data;
  },
  
  getFormasPorAno: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoFormaPagamentoAno[]>(`/analista/${processamentoId}/formas-por-ano`);
    return data;
  },

  getBandeiraForma: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoBandeiraForma[]>(`/analista/${processamentoId}/bandeira-forma`);
    return data;
  },

  getConformidade: async (processamentoId: string) => {
    const { data } = await apiClient.get<ConformidadeBandeiraForma[]>(`/analista/${processamentoId}/conformidade`);
    return data;
  },
};

export const analistaFiltradaApi = {
  getBandeiras: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoBandeira[]>(`/analista-filtrado/${processamentoId}/bandeiras`);
    return data;
  },
  getFormasPagamento: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoFormaPagamento[]>(`/analista-filtrado/${processamentoId}/formas-pagamento`);
    return data;
  },
  getPeriodos: async (processamentoId: string, tipo: 'mes' | 'trimestre' | 'semestre' | 'ano') => {
    const { data } = await apiClient.get<AgregacaoPeriodo[]>(`/analista-filtrado/${processamentoId}/periodos`, { params: { tipo } });
    return data;
  },
  getRecebiveis: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoRecebivel[]>(`/analista-filtrado/${processamentoId}/recebiveis`);
    return data;
  },
  getFormasPorAno: async (processamentoId: string) => {
    const { data } = await apiClient.get<AgregacaoFormaPagamentoAno[]>(`/analista-filtrado/${processamentoId}/formas-por-ano`);
    return data;
  }
};
