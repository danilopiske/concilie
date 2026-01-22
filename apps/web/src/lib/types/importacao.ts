
export interface DeParaRule {
  id: number;
  origem_nome?: string;
  destino_nome: string;
  contexto: string;
  tipo_origem: string; // V, R, L
  tipo_preenchimento: string; // importado, padrao, sistema
  valor_padrao?: string;
  ativo: number; // 1 or 0
  criado_por?: string;
}

export type DeParaCreate = Omit<DeParaRule, 'id'>;

export interface Processamento {
  id: number | string;
  cliente_id?: number;
  tipo_arquivo: string;
  nome_arquivo: string;
  status: 'Pendente' | 'Processando' | 'Sucesso' | 'Erro';
  data_inicio: string;
  data_fim?: string;
  linhas_total: number;
  linhas_processadas: number;
  linhas_sucesso: number;
  linhas_erro: number;
  mensagem_erro?: string;
  
  // Correction Context Fields
  ec_id?: string;
  data_min?: string;
  data_max?: string;
  qtd_processadas?: number;
  qtd_filtradas?: number;
}
