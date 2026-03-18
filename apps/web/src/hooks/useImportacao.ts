
import { useState, useCallback, useEffect } from 'react';
import { importacaoApi } from '@/lib/api/importacao';

export interface ImportTask {
  id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';
  progress: number;
  message: string;
  updated_at: string;
  tipo_arquivo: string;
  contexto: string;
}

export function useImportacao() {
  const [task, setTask] = useState<ImportTask | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);

  const startPolling = useCallback((taskId: string) => {
    setPolling(true);
    const interval = setInterval(async () => {
      try {
        const status = await importacaoApi.getTaskStatus(taskId) as ImportTask;
        setTask(status);

        if (status.status === 'SUCCESS' || status.status === 'FAILED') {
          setPolling(false);
          setLoading(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Erro ao consultar status da importação:', err);
        setPolling(false);
        setLoading(false);
        setError('Erro ao consultar o progresso do processamento.');
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const startImport = useCallback(async (req: {
    file_id: string;
    cliente_id: number;
    ec_id: string;
    contexto: string;
    tipo: string;
    processamentoid?: string;
  }) => {
    try {
      setLoading(true);
      setError(null);
      setTask(null);

      const result = await importacaoApi.confirmarAsync(
        req.file_id,
        req.cliente_id,
        req.ec_id,
        req.contexto,
        req.tipo,
        req.processamentoid
      );

      if (result.task_id) {
        startPolling(result.task_id);
      } else {
        throw new Error('Task ID não retornado pelo servidor.');
      }
    } catch (err: any) {
      console.error('Erro ao iniciar importação:', err);
      setError(err.response?.data?.detail || err.message || 'Erro ao iniciar o processamento.');
      setLoading(false);
    }
  }, [startPolling]);

  const resetTask = useCallback(() => {
    setTask(null);
    setError(null);
    setLoading(false);
    setPolling(false);
  }, []);

  return {
    task,
    loading,
    error,
    polling,
    startImport,
    resetTask,
    setTask,
    setError
  };
}
