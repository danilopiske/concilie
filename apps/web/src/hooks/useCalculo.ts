import { useState, useRef, useEffect } from 'react';
import { calculoApi, CalculoPreviewRequest, CalculoTask } from '@/lib/api/calculo';

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
      const initialTask = await calculoApi.getTaskStatus(task_id);
      setTask(initialTask);
      
      // Start Polling
      startPolling(task_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Erro ao iniciar cálculo');
      setLoading(false);
    }
  };

  const startPolling = (taskId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const currentTask = await calculoApi.getTaskStatus(taskId);
        setTask(currentTask);

        if (currentTask.status === 'SUCCESS' || currentTask.status === 'FAILED') {
          stopPolling();
          setLoading(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        // We don't stop polling on single network error, wait for next cycle
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
