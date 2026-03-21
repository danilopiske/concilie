import { apiClient } from './client';

export const TIPOS_ALERTA = [
  { value: 'variacao_taxa_pct', label: 'Variação de Taxa (%)', unidade: '%' },
  { value: 'importacao_erros_count', label: 'Erros na Importação', unidade: 'erros' },
  { value: 'calculo_divergencia_pct', label: 'Divergência no Cálculo (%)', unidade: '%' },
] as const;

export interface AlertaConfig {
  id: string;
  usuario_id: number | null;
  tipo_alerta: string;
  threshold_valor: number;
  ativo: boolean;
  descricao: string | null;
  created_at: string;
}

export const alertasConfigApi = {
  listar: async () => (await apiClient.get<AlertaConfig[]>('/alertas-config')).data,
  criar: async (body: { tipo_alerta: string; threshold_valor: number; descricao?: string }) =>
    (await apiClient.post<AlertaConfig>('/alertas-config', body)).data,
  atualizar: async (id: string, body: Partial<{ threshold_valor: number; ativo: boolean; descricao: string }>) =>
    (await apiClient.put<AlertaConfig>(`/alertas-config/${id}`, body)).data,
  remover: async (id: string) => { await apiClient.delete(`/alertas-config/${id}`); },
};
