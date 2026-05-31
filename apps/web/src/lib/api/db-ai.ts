import { apiClient } from './client';

export interface ChatSession {
  id: number;
  titulo: string;
  atualizado_em: string;
}

export interface ChatMessageItem {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sql_gerado?: string;
}

export interface MessageResult {
  tipo: 'sql' | 'pergunta' | 'texto';
  resposta: string;
  sql?: string;
  colunas?: string[];
  dados?: Record<string, unknown>[];
  total?: number;
  erro?: string;
}

export const dbAiApi = {
  listSessions: (): Promise<ChatSession[]> =>
    apiClient.get('/ai/sessions').then(r => r.data),

  newSession: (): Promise<ChatSession> =>
    apiClient.post('/ai/sessions').then(r => r.data),

  deleteSession: (id: number): Promise<void> =>
    apiClient.delete(`/ai/sessions/${id}`).then(r => r.data),

  getMessages: (sessionId: number): Promise<ChatMessageItem[]> =>
    apiClient.get(`/ai/sessions/${sessionId}/messages`).then(r => r.data),

  sendMessage: (sessionId: number, pergunta: string, file?: File | null): Promise<MessageResult> => {
    const form = new FormData();
    form.append('pergunta', pergunta);
    if (file) form.append('file', file);
    return apiClient.post(`/ai/sessions/${sessionId}/message`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },
};
