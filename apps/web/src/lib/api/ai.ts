import { apiClient } from './client';

export interface AIAnalysisRequest {
  question: string;
  context_filters?: Record<string, any>;
}

export interface AIAnalysisResponse {
  answer: string;
  chart_data?: any;
  table_data?: any;
  generated_code?: string;
}

export const aiApi = {
  analyze: async (payload: AIAnalysisRequest): Promise<AIAnalysisResponse> => {
    const { data } = await apiClient.post<AIAnalysisResponse>('/ai/analyze', payload);
    return data;
  },
};
