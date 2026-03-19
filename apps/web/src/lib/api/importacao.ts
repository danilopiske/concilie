import { apiClient } from './client';
import { DeParaRule, DeParaCreate, Processamento } from '@/lib/types/importacao';

export const importacaoApi = {
  depara: {
    async listar(clienteId?: number): Promise<DeParaRule[]> {
      const params = clienteId ? { cliente_id: clienteId } : {};
      const { data } = await apiClient.get<DeParaRule[]>('depara/', { params });
      return data;
    },

    async criar(config: DeParaCreate): Promise<DeParaRule> {
      const { data } = await apiClient.post<DeParaRule>('depara/', config);
      return data;
    },

    async atualizar(id: number, config: Partial<DeParaCreate>): Promise<DeParaRule> {
      const { data } = await apiClient.put<DeParaRule>(`depara/${id}`, config);
      return data;
    },

    async deletar(id: number): Promise<void> {
      await apiClient.delete(`depara/${id}`);
    },
  },

  processamentos: {
    async listar(clienteId?: number, status?: string, simple: boolean = false): Promise<Processamento[]> {
      const params: { simple: boolean; cliente_id?: number; status?: string } = { simple };
      if (clienteId) params.cliente_id = clienteId;
      if (status) params.status = status;
      
      const { data } = await apiClient.get<Processamento[]>('processamentos/', { 
        params,
        timeout: 300000 // 5 minutes
      });
      return data;
    },

    async deletarMany(ids: string[]): Promise<void> {
      await apiClient.post('processamentos/batch-delete', ids);
    }
  },

  async upload(
    files: File | File[],
    clienteId: number,
    ecId: string,
    contexto: string,
    tipo: string
  ) {
    const formData = new FormData();
    const fileArray = Array.isArray(files) ? files : [files];
    
    fileArray.forEach(file => {
      formData.append('files', file);
    });
    
    formData.append('cliente_id', clienteId.toString());
    formData.append('ec_id', ecId);
    formData.append('contexto', contexto);
    formData.append('tipo', tipo);

    const { data } = await apiClient.post('importar/upload', formData, {
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
    const { data } = await apiClient.post('importar/confirmar', {
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
  },

  async confirmarAsync(
    fileId: string,
    clienteId: number,
    ecId: string,
    contexto: string,
    tipo: string,
    processamentoid?: number | string
  ) {
    const { data } = await apiClient.post<{ status: string, task_id: string, message: string }>('importacao-async/confirmar', {
        file_id: fileId,
        cliente_id: clienteId,
        ec_id: ecId,
        contexto,
        tipo,
        processamentoid
    });
    return data;
  },

  async uploadAsync(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const { data } = await apiClient.post<{ task_id: string, status_url: string }>('importacao-async/upload/async', formData);
    return data;
  },

  async getTaskStatus(taskId: string) {
    const { data } = await apiClient.get<{
      id: string;
      status: string;
      progress: number;
      message: string;
      updated_at: string;
    }>(`importacao-async/task/${taskId}`);
    return data;
  },

  async getActiveTasks(clienteId: number) {
    const { data } = await apiClient.get<Array<{
      id: string;
      status: string;
      progress: number;
      message: string;
      updated_at: string;
      tipo_arquivo: string;
      contexto: string;
    }>>(`importacao-async/active-tasks`, {
      params: { cliente_id: clienteId }
    });
    return data;
  }
};
