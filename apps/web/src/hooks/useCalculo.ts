import { useState, useRef, useEffect } from 'react';
import { calculoApi, CalculoPreviewRequest, CalculoTask } from '@/lib/api/calculo';

type ApiErr = { response?: { data?: { detail?: string } }; message?: string };

export function useCalculo() {
  const [task, setTask] = useState<CalculoTask | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const startCalculo = async (req: CalculoPreviewRequest) => {
    setLoading(true);
    setError(null);
    setTask(null);

    try {
      const { task_id } = await calculoApi.processarAsync(req);
      // Start polling immediately — don't await initial status (DB may be busy)
      startPolling(task_id);
    } catch (err: unknown) {
      setError((err as ApiErr)?.response?.data?.detail || (err as ApiErr)?.message || 'Erro ao iniciar cálculo');
      setLoading(false);
    }
  };

  const startPolling = (taskId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const currentTask = await calculoApi.getTaskStatus(taskId);
        setError(null); // clear any previous transient error
        setTask(currentTask);

        if (currentTask.status === 'SUCCESS' || currentTask.status === 'FAILED') {
          stopPolling();
          setLoading(false);
        }
      } catch (err: unknown) {
        const msg = (err as ApiErr)?.response?.data?.detail || (err as ApiErr)?.message || 'Erro na comunicação com o servidor';
        setError(`Aguardando servidor... (${msg})`);
        console.error('Polling error:', err);
        // Don't stop polling — backend may still be processing
      }
    }, 2000); // 2 seconds
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
    startCalculo,
    resetTask: () => setTask(null)
  };
}
