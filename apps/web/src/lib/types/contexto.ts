/**
 * Types para Contextos
 */

export interface Contexto {
  id: number;
  nome: string;
  descricao?: string | null;
  ativo: boolean;
  criado_por?: string | null;
  criado_em?: string;
  atualizado_em?: string;
}

export interface ContextoCreate {
  nome: string;
  descricao?: string;
  ativo?: boolean;
  criado_por?: string;
}

export interface ContextoUpdate {
  nome?: string;
  descricao?: string;
  ativo?: boolean;
}
