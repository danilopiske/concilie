/**
 * Tipos de Gestão
 * Baseado nos schemas Pydantic do backend
 */

export interface Endereco {
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf_id?: string;
  cep?: string;
}

export interface Contatos {
  telefone1?: string;
  telefone2?: string;
  telefone3?: string;
  email1?: string;
  email2?: string;
}

export interface Bancario {
  banco?: string;
  agencia?: string;
  conta?: string;
}

export interface Cliente {
  cliente_id: number;
  nome_fantasia: string | null;
  razao_social: string | null;
  cnpj: string | null;
  endereco?: Endereco;
  contatos?: Contatos;
  bancario?: Bancario;
  ecs?: string[];
}

export interface Contexto {
  id: number;
  nome: string;
  descricao?: string;
  ativo: boolean;
  criado_por?: string;
  criado_em?: string;
  atualizado_em?: string;
}

export interface ContextoCreate {
  nome: string;
  descricao?: string;
  ativo?: boolean;
}

export interface BandeiraDisponivel {
  id: number;
  nome: string;
  padrao: boolean;
}

export interface BandeiraCreate {
  nome: string;
  padrao?: boolean;
}

export interface TermoFiltravel {
  id: number;
  ec: string;
  termo: string;
  tipo: string;
  contexto: string;
}

export interface TermoCreate {
  termo: string;
  tipo: 'v' | 'r' | 'l' | 'status';
}

export interface TaxaResponse {
  id: number;
  ec: string;
  contexto_id: number;
  bandeira: string;
  forma_pagamento: string;
  parcelado: string;
  parcela_ini: number;
  parcela_fim: number;
  taxa: number;
  data_ini: string;
  data_fim: string;
}

export interface TaxaCreate {
  contexto_id?: number;
  bandeira?: string;
  forma_pagamento?: string;
  parcelado?: string;
  parcela_ini?: number;
  parcela_fim?: number;
  taxa: number;
  data_ini?: string;
  data_fim?: string;
}

export interface CopiarTaxasRequest {
  ec_origem_id: number;
  ecs_destino_ids: number[];
  sobrescrever: boolean;
}

export type ClienteDetalhado = Cliente;
export type ClienteCreate = Cliente;
export type EC = string;
export type Taxa = TaxaResponse;
