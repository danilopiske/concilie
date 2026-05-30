export interface DeParaRule {
  id: number;
  origem_nome: string;
  destino_nome: string;
  contexto: string;
  tipo_origem: string;
  tipo_preenchimento: string;
  valor_padrao?: string;
  ativo: number;
  criado_por?: string;
}

export interface DeParaCreate {
  origem_nome: string;
  destino_nome: string;
  contexto: string;
  tipo_origem?: string;
  tipo_preenchimento?: string;
  valor_padrao?: string;
  ativo?: number;
}

export interface Processamento {
  id: number | string;
  data_inicio: string;
  cliente_id?: number;
  status: string;
  nome_arquivo: string;
  tipo_arquivo: string;
  linhas_processadas?: number;
  linhas_total?: number;
  linhas_sucesso?: number;
  linhas_erro?: number;
  mensagem_erro?: string;
  
  // Campos de contexto de Correção
  ec_id?: string;
  contexto?: string;
  data_min?: string;
  data_max?: string;
  qtd_processadas?: number;
  qtd_filtradas?: number;
}

export interface ImportTask {
    id: string;
    type: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    created_at: string;
    updated_at?: string;
    metadata: Record<string, unknown>;
    result?: {
        rows_processed: number;
        columns: string[];
        file_path: string;
        // For depara logic
        headers?: string[];
    };
    error?: string;
    progress: number;
}
