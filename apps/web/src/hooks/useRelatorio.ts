import { useState, useRef, useEffect } from 'react';
import { relatorioApi, RelatorioRequest, RelatorioTask } from '@/lib/api/relatorio';

export function useRelatorio() {
  const [task, setTask] = useState<RelatorioTask | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const startGeracao = async (req: RelatorioRequest) => {
    setLoading(true);
    setError(null);
    setTask(null);

    try {
      const { task_id } = await relatorioApi.gerarAsync(req);
      const initialTask = await relatorioApi.getTaskStatus(task_id);
      setTask(initialTask);
      
      // Start Polling
      startPolling(task_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao iniciar geração do relatório');
      setLoading(false);
    }
  };

  const startPolling = (taskId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const currentTask = await relatorioApi.getTaskStatus(taskId);
        setTask(currentTask);

        if (currentTask.status === 'SUCCESS' || currentTask.status === 'FAILED') {
          stopPolling();
          setLoading(false);
          
          if (currentTask.status === 'FAILED') {
            setError(currentTask.message);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 5000); // 5 seconds (optimized for lower server load)
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  return {
    task,
    loading,
    error,
    startGeracao,
    resetTask: () => {
        setTask(null);
        setError(null);
    }
  };
}
