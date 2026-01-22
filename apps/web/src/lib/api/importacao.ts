import { apiClient } from './client';
import { DeParaRule, DeParaCreate, Processamento } from '@/lib/types/importacao';

export const importacaoApi = {
  depara: {
    async listar(clienteId?: number): Promise<DeParaRule[]> {
      const params = clienteId ? { cliente_id: clienteId } : {};
      const { data } = await apiClient.get<DeParaRule[]>('/depara/', { params });
      return data;
    },

    async criar(config: DeParaCreate): Promise<DeParaRule> {
      const { data } = await apiClient.post<DeParaRule>('/depara/', config);
      return data;
    },

    async atualizar(id: number, config: Partial<DeParaCreate>): Promise<DeParaRule> {
      const { data } = await apiClient.put<DeParaRule>(`/depara/${id}`, config);
      return data;
    },

    async deletar(id: number): Promise<void> {
      await apiClient.delete(`/depara/${id}`);
    },
  },

  processamentos: {
    async listar(clienteId?: number, status?: string, simple: boolean = false): Promise<Processamento[]> {
      const params: any = { simple };
      if (clienteId) params.cliente_id = clienteId;
      if (status) params.status = status;
      
      const { data } = await apiClient.get<Processamento[]>('/processamentos/', { params });
      return data;
    },
  },

  async upload(
    file: File,
    clienteId: number,
    ecId: string,
    contexto: string,
    tipo: string
  ) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('cliente_id', clienteId.toString());
    formData.append('ec_id', ecId);
    formData.append('contexto', contexto);
    formData.append('tipo', tipo);

    const { data } = await apiClient.post('/importacao/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, 
    });
    return data;
  },

  async confirmar(
    fileId: string,
    clienteId: number,
    ecId: string,
    contexto: string,
    tipo: string,
    processamentoid?: number | string
  ) {
    const { data } = await apiClient.post('/importacao/confirmar', {
        file_id: fileId,
        cliente_id: clienteId,
        ec_id: ecId,
        contexto,
        tipo,
        processamentoid
    }, {
        timeout: 300000 // 5 minutos
    });
    return data;
  }
};
