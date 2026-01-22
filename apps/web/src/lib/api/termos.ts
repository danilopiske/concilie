/**
 * API Client - Termos Filtráveis
 */

import { apiClient } from './client';

export interface TermoFiltravel {
  id: number;
  ec: string;
  termo: string;
  tipo: string;
  contexto: string;
}

export interface TermoFiltravelCreate {
  ec: string;
  termo: string;
  tipo: string;
  contexto: string;
}

/**
 * Listar termos filtráveis por EC e contexto
 */
export async function listarTermos(
  ec: string,
  contexto: string = 'padrao',
  tipo?: string
): Promise<TermoFiltravel[]> {
  const params = new URLSearchParams({ contexto });
  if (tipo) params.append('tipo', tipo);
  
  const { data } = await apiClient.get<TermoFiltravel[]>(
    `/termos/${ec}?${params.toString()}`
  );
  return data;
}

/**
 * Adicionar novo termo filtrável
 */
export async function adicionarTermo(
  termo: TermoFiltravelCreate
): Promise<TermoFiltravel> {
  const { data } = await apiClient.post<TermoFiltravel>('/termos/', termo);
  return data;
}

/**
 * Excluir termo filtrável
 */
export async function excluirTermo(termoId: number): Promise<void> {
  await apiClient.delete(`/termos/${termoId}`);
}
