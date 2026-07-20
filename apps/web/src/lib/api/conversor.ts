import { API_URL } from '@/lib/api/client';

export async function converterRedeFiles(files: File[]): Promise<Blob> {
  const form = new FormData();
  files.forEach(f => form.append('files', f));

  const res = await fetch(`${API_URL}/api/v1/conversor/rede`, {
    method: 'POST',
    body: form,
    credentials: 'include',
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Erro desconhecido' }));
    throw new Error(err.detail || `Erro ${res.status}`);
  }

  return res.blob();
}
