
import { useState, useCallback, useRef, useEffect } from 'react';
import { importacaoApi } from '@/lib/api/importacao';
import { ImportTask } from '@/lib/types/importacao';

type ApiTaskStatus = {
  id: string;
  status: string;
  progress: number;
  message: string;
  updated_at: string;
  result?: ImportTask['result'];
  error?: string;
};

interface UseFileImportResult {
    upload: (file: File) => Promise<void>;
    status: ImportTask['status'] | 'idle';
    progress: number;
    result: ImportTask['result'] | null;
    error: string | null;
    isUploading: boolean;
    reset: () => void;
}

export function useFileImport(): UseFileImportResult {
    const [status, setStatus] = useState<ImportTask['status'] | 'idle'>('idle');
    const [progress, setProgress] = useState(0);
    const [result, setResult] = useState<ImportTask['result'] | null>(null);
    const [error, setError] = useState<string | null>(null);
    const pollInterval = useRef<NodeJS.Timeout | null>(null);

    const cleanup = useCallback(() => {
        if (pollInterval.current) {
            clearInterval(pollInterval.current);
            pollInterval.current = null;
        }
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return cleanup;
    }, [cleanup]);

    const pollStatus = useCallback(async (taskId: string) => {
        try {
            const task = await importacaoApi.getTaskStatus(taskId) as ApiTaskStatus;

            setStatus(task.status as ImportTask['status']);
            setProgress(task.progress);

            if (task.status === 'completed') {
                setResult(task.result || null);
                cleanup();
            } else if (task.status === 'failed') {
                setError(task.error || 'Unknown error');
                cleanup();
            }
        } catch (err) {
            setError('Failed to check upload status');
            cleanup();
        }
    }, [cleanup]);

    const upload = useCallback(async (file: File) => {
        try {
            setStatus('pending');
            setError(null);
            setProgress(0);
            setResult(null);

            // 1. Start Async Upload
            const { task_id } = await importacaoApi.uploadAsync(file);

            // 2. Start Polling
            setStatus('processing');
            pollInterval.current = setInterval(() => pollStatus(task_id), 1000); // Poll every 1s

        } catch (err: unknown) {
            setStatus('failed');
            setError((err as Error)?.message || 'Failed to start upload');
        }
    }, [pollStatus]);

    const reset = useCallback(() => {
        cleanup();
        setStatus('idle');
        setProgress(0);
        setResult(null);
        setError(null);
    }, [cleanup]);

    return {
        upload,
        status,
        progress,
        result,
        error,
        isUploading: status === 'pending' || status === 'processing',
        reset
    };
}
