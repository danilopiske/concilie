/**
 * API de Gestão - Endpoints para gerenciar Clientes, ECs, Contextos, Bandeiras, Termos, Taxas
 * Conversão direta dos endpoints FastAPI criados
 */
import { apiClient } from './client';
import {
  Cliente,
  ClienteDetalhado,
  ClienteCreate,
  EC,
  Contexto,
  ContextoCreate,
  BandeiraDisponivel,
  BandeiraCreate,
  TermoFiltravel,
  TermoCreate,
  Taxa,
  TaxaCreate,
  CopiarTaxasRequest,
} from '@/lib/types/gestao';

export const gestaoApi = {
  // ============ CLIENTES ============
  clientes: {
    async listar(): Promise<Cliente[]> {
      const { data } = await apiClient.get<Cliente[]>('/clientes');
      return data;
    },

    async obter(clienteId: number): Promise<ClienteDetalhado> {
      const { data } = await apiClient.get<ClienteDetalhado>(`/clientes/${clienteId}`);
      return data;
    },

    async criar(cliente: ClienteCreate): Promise<ClienteDetalhado> {
      const { data } = await apiClient.post<ClienteDetalhado>('/clientes', cliente);
      return data;
    },

    async atualizar(clienteId: number, cliente: Partial<ClienteCreate>): Promise<ClienteDetalhado> {
      const { data } = await apiClient.put<ClienteDetalhado>(`/clientes/${clienteId}`, cliente);
      return data;
    },

    async deletar(clienteId: number): Promise<void> {
      await apiClient.delete(`/clientes/${clienteId}`);
    },

    async listarECs(clienteId: number): Promise<EC[]> {
      const { data } = await apiClient.get<EC[]>(`/clientes/${clienteId}/ecs`);
      return data;
    },
  },

  // ============ CONTEXTOS ============
  contextos: {
    async listar(incluirInativos: boolean = false): Promise<Contexto[]> {
      const { data } = await apiClient.get<Contexto[]>('/contextos', {
        params: { incluir_inativos: incluirInativos },
      });
      return data;
    },

    async obter(contextoId: number): Promise<Contexto> {
      const { data } = await apiClient.get<Contexto>(`/contextos/${contextoId}`);
      return data;
    },

    async criar(contexto: ContextoCreate): Promise<Contexto> {
      const { data } = await apiClient.post<Contexto>('/contextos', contexto);
      return data;
    },

    async atualizar(contextoId: number, contexto: Partial<ContextoCreate>): Promise<Contexto> {
      const { data } = await apiClient.put<Contexto>(`/contextos/${contextoId}`, contexto);
      return data;
    },

    async deletar(contextoId: number): Promise<void> {
      await apiClient.delete(`/contextos/${contextoId}`);
    },
  },

  // ============ BANDEIRAS DISPONÍVEIS ============
  bandeiras: {
    async listar(): Promise<BandeiraDisponivel[]> {
      const { data } = await apiClient.get<BandeiraDisponivel[]>('/gestao/bandeiras-disponiveis');
      return data;
    },

    async criar(bandeira: BandeiraCreate): Promise<BandeiraDisponivel> {
      const { data } = await apiClient.post<BandeiraDisponivel>('/gestao/bandeiras-disponiveis', bandeira);
      return data;
    },

    async deletar(bandeiraId: number): Promise<void> {
      await apiClient.delete(`/gestao/bandeiras-disponiveis/${bandeiraId}`);
    },
  },

  // ============ BANDEIRAS POR EC ============
  bandeirasPorEC: {
    async obter(ecId: string | number): Promise<Record<string, number>> {
      const { data } = await apiClient.get<Record<string, number>>(`/gestao/ecs/${ecId}/bandeiras`);
      return data;
    },

    async atualizar(ecId: string | number, bandeiras: Record<string, number>): Promise<void> {
      await apiClient.put(`/gestao/ecs/${ecId}/bandeiras`, { bandeiras });
    },
  },

  // ============ TERMOS FILTRÁVEIS ============
  termos: {
    async listar(ecId: string | number): Promise<TermoFiltravel[]> {
      const { data } = await apiClient.get<TermoFiltravel[]>(`/gestao/ecs/${ecId}/termos`);
      return data;
    },

    async adicionar(ecId: string | number, termo: TermoCreate): Promise<TermoFiltravel> {
      const { data } = await apiClient.post<TermoFiltravel>(`/gestao/ecs/${ecId}/termos`, termo);
      return data;
    },

    async excluir(ecId: string | number, termoId: number): Promise<void> {
      await apiClient.delete(`/gestao/ecs/${ecId}/termos/${termoId}`);
    },
  },

  // ============ TAXAS ============
  taxas: {
    async listar(ecId: string | number): Promise<Taxa[]> {
      const { data } = await apiClient.get<Taxa[]>(`/gestao/ecs/${ecId}/taxas`);
      return data;
    },

    async adicionar(ecId: string | number, taxa: TaxaCreate): Promise<Taxa> {
      const { data } = await apiClient.post<Taxa>(`/gestao/ecs/${ecId}/taxas`, taxa);
      return data;
    },

    async excluir(ecId: string | number, taxaId: number): Promise<void> {
      await apiClient.delete(`/gestao/ecs/${ecId}/taxas/${taxaId}`);
    },

    async copiar(request: CopiarTaxasRequest): Promise<void> {
      await apiClient.post('/gestao/taxas/copiar', request);
    },
  },
};
