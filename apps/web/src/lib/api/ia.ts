import apiClient from './client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  mensagem: string;
  processamento_id?: string;
  cliente_id?: number;
  historico: ChatMessage[];
}

export interface ChatResponse {
  resposta: string;
  dados_contexto?: Record<string, unknown>;
  sugestoes: string[];
}

export const iaApi = {
  chat: async (req: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/ia/chat', req);
    return response.data;
  },
};
