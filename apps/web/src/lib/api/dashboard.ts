import { apiClient } from './client';

export interface DashboardResumo {
  total_processamentos: number;
  processamentos_mes_atual: number;
  valor_total_conciliado: number;
  alertas_abusividade_pendentes: number;
  extratos_divergentes: number;
  extratos_aguardando: number;
  relatorios_gerados_mes: number;
  ultimo_processamento: {
    id: number;
    nome_arquivo: string;
    status: string;
    data: string | null;
  } | null;
}

export interface EventoAtividade {
  tipo: 'importacao' | 'calculo' | 'relatorio' | 'abusividade' | 'extrato';
  descricao: string;
  cliente_nome: string;
  created_at: string;
  status: 'ok' | 'alerta' | 'erro';
}

export interface AtividadeRecenteResponse {
  eventos: EventoAtividade[];
}

export interface AtividadeSemanal {
  label: string;
  count: number;
}

export interface AtividadeSemanalResponse {
  semanas: AtividadeSemanal[];
}

export const dashboardApi = {
  getResumo: (periodo: number = 30): Promise<DashboardResumo> =>
    apiClient.get('/dashboard/resumo', { params: { periodo } }).then((r) => r.data),

  getAtividadeRecente: (): Promise<AtividadeRecenteResponse> =>
    apiClient.get('/dashboard/atividade-recente').then((r) => r.data),

  getAtividadeSemanal: (): Promise<AtividadeSemanalResponse> =>
    apiClient.get('/dashboard/atividade-semanal').then((r) => r.data),
};
