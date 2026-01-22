export interface ResumoItem {
    valor: string;
    quantidade: number;
    valor_total: number;
}

export interface HistoricoItem {
    id: number;
    data_correcao: string;
    usuario: string;
    tipo_correcao: string;
    valor_antigo?: string;
    valor_novo?: string;
    linhas_afetadas: number;
}

export interface ResumoResponse {
    formas_pagamento: ResumoItem[];
    bandeiras: ResumoItem[];
    status: ResumoItem[];
    recebiveis: ResumoItem[];
}

export interface AtualizarRequest {
    processamento_id: string;
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento';
    valor_antigo: string;
    valor_novo: string;
}

export interface RemoverRequest {
    processamento_id: string;
    campo: 'forma_pagamento' | 'bandeira' | 'status' | 'lancamento';
    valor: string;
}
